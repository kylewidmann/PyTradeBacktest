from typing import Type

from pytrade.indicator import Indicator
from pytrade.strategy import FxStrategy

from pytradebacktest.broker import BacktestBroker
from pytradebacktest.data import MarketData


class Backtest:

    def __init__(
        self,
        data: MarketData,
        kstrategy: Type[FxStrategy],
        cash: float,
        comission: float = 0.0,
        margin: float = 1.0,
    ):
        self.data = data
        self.kstrategy = kstrategy
        self.cash = cash
        self.comission = comission
        self.margin = margin

    async def run(self):

        # Monkey patch indicators so their update does not
        # need to recalculate after each increment, instead
        # store their initial values from the full data context
        # and then increment based on the current context length
        def increment_indicator(self):
            if not hasattr(self, "_backtest_values"):
                self._backtest_values = self._values.copy()
            self._values = self._backtest_values[: len(self._data)]

        Indicator._update = increment_indicator

        broker = BacktestBroker(self.data, self.cash, self.comission, self.margin)

        strategy = self.kstrategy(broker, self.data)
        strategy.init()

        while self.data.next():

            broker.next()
            strategy.next()

        # Increment data points
        # Update indicators
        # Update trades
        # Claculate results/stats

    def plot(self):
        pass
