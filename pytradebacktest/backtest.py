from typing import Type

from pytrade.strategy import FxStrategy

from pytradebacktest.broker import BacktestBroker
from pytradebacktest.data import MarketData
from pytradebacktest.strategy import BacktestStrategyWrapper


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

        broker = BacktestBroker(self.data)

        strategy = BacktestStrategyWrapper(broker, self.data, self.kstrategy)
        strategy.init()

        while self.data.next():

            broker.next()
            await strategy.next()

        # Increment data points
        # Update indicators
        # Update trades
        # Claculate results/stats
        pass

    def plot(self):
        pass
