from math import copysign

import numpy as np
from pytrade.broker import Order

from pytradebacktest.data import InstrumentData


class OrderContext:

    def __init__(
        self,
        order: Order,
        data: InstrumentData,
        trade_on_close: bool,
        commission: float,
        leverage: float,
        margin_available: float,
    ):
        self._order = order
        self._data = data
        self._trade_on_close = trade_on_close
        self._commission = commission
        self._leverage = leverage
        self._margin_availalbe = margin_available

    @property
    def order(self):
        return self._order

    @property
    def data(self):
        return self._data

    @property
    def open(self):
        return self._data.Open.iloc[-1]

    @property
    def high(self):
        return self._data.High.iloc[-1]

    @property
    def low(self):
        return self._data.Low.iloc[-1]

    @property
    def close(self):
        return self._data.Close.iloc[-1]

    @property
    def prev_close(self):
        return self._data.Close.iloc[-1]

    @property
    def timestmap(self):
        return self._data.timestamp

    @property
    def entry_time(self):
        return (
            self._data.prev_timestamp
            if self.is_market_order and self._trade_on_close
            else self._data.timestamp
        )

    @property
    def is_market_order(self):
        return not self.order.limit and not self.order.stop

    @property
    def entry_price(self):
        if self.order.limit:
            func = min if self.order.is_long else max
            price = func(self.order.stop or self.open, self.order.limit)
        else:
            price = self.prev_close if self._trade_on_close else self.open
            func = max if self.order.is_long else min
            stop_default = -np.inf if self.order.is_long else np.inf
            price = func(price, self.order.stop or stop_default)
        return price

    @property
    def adjusted_entry_price(self):
        # Need to update to account for currency pairs and base vs counter currency
        # as well as spread
        return self.entry_price * (1 + copysign(self._commission, self.order.size))

    @property
    def adjusted_size(self):
        order = self.order
        _size = order.size
        if -1 < _size < 1:
            _size = copysign(
                int(
                    (self._margin_availalbe * self._leverage * abs(order.size))
                    // self.adjusted_entry_price
                ),
                order.size,
            )

        return _size
