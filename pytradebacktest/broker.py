from typing import Optional

import numpy as np
from pandas import Timestamp
from pytrade.instruments import MINUTES_MAP, Granularity, Instrument
from pytrade.interfaces.broker import IBroker
from pytrade.interfaces.data import IInstrumentData
from pytrade.models import Order, Trade

from pytradebacktest.data import MarketData
from pytradebacktest.exceptions import OutOfMoneyError
from pytradebacktest.order import OrderContext
from pytradebacktest.position import Position


class BacktestBroker(IBroker):
    def __init__(
        self,
        data: MarketData,
        cash,
        commission,
        margin,
        trade_on_close=False,
        hedging=False,
        exclusive_orders=False,
        spread=0.0,
    ):
        self._data = data
        self._cash = cash
        self._commission = commission
        self._leverage = 1 / margin
        self._trade_on_close = trade_on_close
        self._hedging = hedging
        self._exclusive_orders = exclusive_orders
        self._spread = spread

        self._equity = np.tile(np.nan, len(self._data))
        self.orders: list[Order] = []
        self.trades: list[Trade] = []
        self.positions: list[Position] = []
        self.closed_trades: list[Trade] = []

    @property
    def equity(self) -> float:
        return self._cash + sum(trade.pl for trade in self.trades)

    @property
    def margin_available(self) -> float:
        margin_used = sum(trade.value / self._leverage for trade in self.trades)
        return max(0, self.equity - margin_used)

    @property
    def leverage(self) -> float:
        return self._leverage

    def order(self, order: Order):
        # If exclusive orders (each new order auto-closes previous orders/position),
        # cancel all non-contingent orders and close all open trades beforehand
        if self._exclusive_orders:
            for o in list(self.orders):
                if not o.is_contingent:
                    self.orders.remove(o)
            for t in self.trades:
                self.orders.insert(0, Order(t.instrument, -t.size))

        self.orders.append(order)

    def load_instrument_candles(self, instrument: Instrument, granularity: Granularity, count: int):
        self._data.load_instrument_candles(instrument, granularity, count)

    def subscribe(self, instrument: Instrument, granularity: Granularity) -> IInstrumentData:
        return self._data.get(instrument, granularity)

    def get_position(self, instrument: Instrument) -> Position:
        return Position(instrument, self.trades)

    def close_position(self, instrument: Instrument):
        position = self.get_position(instrument)
        for trade in position.trades:
            self.orders.insert(0, Order(trade.instrument, -trade.size, parent_trade=trade))

    def next(self):
        self._process_orders()
        self._update_equity()

    def _update_equity(self):
        # Update equity
        equity = self.equity
        i = self._data.i

        self._equity[i] = equity
        # If equity is negative, set all to 0 and stop the simulation
        if equity <= 0:
            if self.margin_available > 0:
                raise RuntimeError
            for trade in self.trades:
                _data = self._get_instrument_data(trade.instrument)
                self._close_trade(trade, _data.Close.iloc[-1], _data.timestamp)
            self._cash = 0
            self._equity[i:] = 0
            raise OutOfMoneyError

    def _process_orders(self):
        reprocess_orders = False
        for order in list(self.orders):
            _data = self._get_instrument_data(order.instrument)

            ctx = OrderContext(
                order,
                _data,
                self._trade_on_close,
                self._commission,
                self._leverage,
                self.margin_available,
                self._spread,
            )
            # Related SL/TP order already removed
            if order not in self.orders:
                continue

            if order.stop:
                stop_hit = self._evaluate_stop_order(ctx)
                if not stop_hit:
                    continue

            if order.limit:
                limit_hit, limit_hit_before_stop = self._evaluate_limit_order(ctx)
                if not limit_hit or limit_hit_before_stop:
                    continue

            if order.is_contingent:
                self._process_contingent_order(ctx)
            else:
                new_trade = self._process_market_order(ctx)

                if new_trade and (order.stop_loss_on_fill or order.take_profit_on_fill):
                    # Need to reprocess since we created a contingent order that could
                    # hit within the same bar
                    reprocess_orders = True

        if reprocess_orders:
            self._process_orders()

    def _evaluate_stop_order(self, ctx: OrderContext):
        order: Order = ctx.order
        stop_hit = False
        stop_hit = (ctx.high > order.stop) if order.is_long else (ctx.low < order.stop)

        return stop_hit

    def _evaluate_limit_order(self, ctx: OrderContext):
        order = ctx.order
        limit_hit = False
        limit_hit = ctx.low < order.limit if order.is_long else ctx.high > order.limit
        limit_hit_before_stop = limit_hit and (
            order.limit < (order.stop or -np.inf)
            if order.is_long
            else order.limit > (order.stop or np.inf)
        )

        return limit_hit, limit_hit_before_stop

    def _process_contingent_order(self, ctx: OrderContext):
        order = ctx.order
        trade = ctx.order.parent_trade
        _order_size = ctx.adjusted_size

        if trade in self.trades:
            closed = self._reduce_trade(trade, _order_size, ctx.entry_price, ctx.entry_time)
            # If this is a SL/TP closing the trade already removed it.
            if closed and order in self.orders:
                self.orders.remove(order)

    def _process_market_order(self, ctx: OrderContext):
        order = ctx.order
        _order_size = ctx.adjusted_size
        new_trade = False
        if not self._hedging:
            _order_size = self._update_position(ctx)
            order.resize(_order_size)

        # IF we have the margin to cover the order
        _insufficent_funds = (
            abs(_order_size) * ctx.entry_price > self.margin_available * self._leverage
        )
        if _order_size and not _insufficent_funds:
            self._open_trade(ctx)
            new_trade = True

        if _insufficent_funds:
            pass

        self.orders.remove(order)

        return new_trade

    def _update_position(self, ctx: OrderContext):
        order = ctx.order
        _need_size = ctx.adjusted_size
        # Fill position by FIFO closing/reducing existing opposite-facing trades.
        # Existing trades are closed at unadjusted price, because the adjustment
        # was already made when buying.
        for trade in list(self.trades):
            opposing = trade.is_long != order.is_long
            same_instrument = trade.instrument == order.instrument
            if not opposing or not same_instrument:
                continue

            # Order is equal or larger so close trade
            if abs(_need_size) >= abs(trade.size):
                self._close_trade(trade, ctx.entry_price, ctx.timestmap)
                _need_size += trade.size
            else:
                self._reduce_trade(trade, _need_size, ctx.entry_price, ctx.timestmap)
                _need_size = 0

            if not _need_size:
                break

        return _need_size

    def _open_trade(self, ctx: OrderContext, tag: Optional[str] = None):
        order = ctx.order
        size = ctx.adjusted_size
        trade = Trade(order.instrument, size, ctx.entry_price, ctx.entry_time, ctx.data, tag)
        self.trades.append(trade)

        if order.take_profit_on_fill:
            tp_order = Order(
                order.instrument,
                -order.size,
                limit=order.take_profit_on_fill,
                parent_trade=trade,
            )
            trade.tp = tp_order
            self.orders.insert(0, tp_order)

        if order.stop_loss_on_fill:
            sl_order = Order(
                order.instrument,
                -order.size,
                stop=order.stop_loss_on_fill,
                parent_trade=trade,
            )
            trade.sl = sl_order
            self.orders.insert(0, sl_order)

    def _reduce_trade(self, trade: Trade, size: int, price: float, timestamp: Timestamp):
        size_left = trade.size + size
        closed = False

        if not size_left:
            close_trade = trade
            closed = True
        else:
            trade.reduce(size_left)
            if trade.sl is not None:
                trade.sl.resize(-size_left)
            if trade.tp is not None:
                trade.tp.resize(-size_left)

            close_trade = Trade(
                trade.instrument, size, trade.entry_price, trade.entry_time, trade.data
            )
            self.trades.append(close_trade)

        self._close_trade(close_trade, price, timestamp)
        return closed

    def close_trades(self):
        for trade in self.trades:
            self.orders.insert(0, Order(trade.instrument, -trade.size, parent_trade=trade))

    def _close_trade(self, trade: Trade, price: float, timestamp: Timestamp):
        self.trades.remove(trade)
        if trade.sl is not None:
            self.orders.remove(trade.sl)
        if trade.tp is not None:
            self.orders.remove(trade.tp)

        trade.close(price, timestamp)
        self.closed_trades.append(trade)
        self._cash += trade.pl

    def _get_instrument_data(self, instrument: Instrument):
        _instrument_data = [
            src
            for src in self._data._sources
            if src.instrument == instrument and self._data.index == src.index
        ]
        _instrument_data.sort(key=lambda src: MINUTES_MAP[src.granularity])
        _data = _instrument_data[0]
        return _data
