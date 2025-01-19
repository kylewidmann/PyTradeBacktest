from typing import Callable

from pytrade.interfaces.broker import IBroker
from pytrade.interfaces.data import IInstrumentData
from pytrade.models.broker import Trade
from pytrade.models.instruments import Candlestick, FxInstrument, Granularity
from pytrade.models.order import Order, OrderRequest
from pytrade.models.position import Position

from pytradebacktest.data import MarketData


class BacktestBroker(IBroker):

    def __init__(
        self,
        data: MarketData,
        cash,
        commission,
        margin,
        trade_on_close = False,
        hedging = False,
        exclusive_orders = False,
    ):
        self._data = data
        self._cash = cash
        self._commission = commission
        self._leverage = 1 / margin
        self._trade_on_close = trade_on_close
        self._hedging = hedging
        self._exclusive_orders = exclusive_orders

        self._equity = 0
        self.orders: list[Order] = []
        self.trades: list[Trade] = []
        self.position = Position(self)
        self.closed_trades: list[Trade] = []

    @property
    def equity(self) -> float:
        return self._cash + sum(trade.pl for trade in self.trades)

    @property
    def margin_available(self) -> float:
        margin_used = sum(trade.value / self._leverage for trade in self.trades)
        return max(0, self.equity - margin_used)

    def order(self, order: OrderRequest):

        # Put the new order in the order queue,
        # inserting SL/TP/trade-closing orders in-front
        sl_tp_close = False
        if sl_tp_close:
            self.orders.insert(0, order)
        else:
            # If exclusive orders (each new order auto-closes previous orders/position),
            # cancel all non-contingent orders and close all open trades beforehand
            # if self._exclusive_orders:
            #     for o in self.orders:
            #         if not o.is_contingent:
            #             o.cancel()
            #     for t in self.trades:
            #         t.close()

            self.orders.append(order)

    def subscribe(
        self,
        instrument: FxInstrument,
        granularity: Granularity
    ) -> IInstrumentData:
        return self._data.get(instrument, granularity)

    def next(self):
        self._process_orders()
        # equity = self.equity

        # Update equity

        # self._equity[] = self.equity
        # # If equity is negative, set all to 0 and stop the simulation
        # if equity <= 0:
        #     assert self.margin_available <= 0
        #     for trade in self.trades:
        #         self._close_trade(trade, self._data.Close[-1], i)
        #     self._cash = 0
        #     self._equity[i:] = 0
        #     raise _OutOfMoneyError

    def _process_orders(self):

        for order in list(self.orders):

            # Related SL/TP order already removed
            if order not in self.orders:
                continue

            # if order.stop and self._hit_stop(order):
            #     pass

            # if order.limit and self._hit_limit(order):
            #     pass
