from typing import Callable

from pytrade.interfaces.broker import IBroker
from pytrade.models.instruments import Candlestick, Granularity, Instrument
from pytrade.models.order import OrderRequest

from pytradebacktest.data import MarketData


class BacktestBroker(IBroker):

    def __init__(self, data: MarketData):
        self.data = data

    @property
    def equity(self) -> float:
        return 0
        return self._cash + sum(trade.pl for trade in self.trades)

    @property
    def margin_available(self) -> float:
        return 0
        # From https://github.com/QuantConnect/Lean/pull/3768
        margin_used = sum(trade.value / self._leverage for trade in self.trades)
        return max(0, self.equity - margin_used)

    def order(self, order: OrderRequest):
        pass

    def subscribe(
        self,
        instrument: Instrument,
        granularity: Granularity,
        callback: Callable[[Candlestick], None],
    ):
        pass

    def next(self):
        pass
