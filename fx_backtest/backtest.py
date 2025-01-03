from typing import Type
from fx_lib.strategy import FxStrategy

from fx_backtest.broker import BacktestBroker
from fx_backtest.data import MarketData

from fx_backtest.strategy import BacktestStrategyWrapper


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
