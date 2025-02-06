from typing import Type

import pandas as pd
from progressbar import ProgressBar
from pytrade.indicator import Indicator
from pytrade.instruments import Granularity
from pytrade.strategy import FxStrategy

from pytradebacktest.broker import BacktestBroker
from pytradebacktest.data import MarketData
from pytradebacktest.plot import plot
from pytradebacktest.stats import Stats


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

        self.broker = BacktestBroker(self.data, self.cash, self.comission, self.margin)

        strategy = self.kstrategy(self.broker, self.data)
        strategy.init()

        with ProgressBar(max_value=len(self.data), redirect_stdout=True) as bar:
            while self.data.next():

                self.broker.next()
                strategy.next()

                bar.next()

        # Close any open trades:
        self.broker.close_trades()
        # Call broker one last time to clean up any outstanding orders from strategy
        self.broker.next()

        # Claculate results/stats
        equity = pd.Series(self.broker._equity).bfill().fillna(self.broker._cash).values
        return Stats(self.broker.closed_trades, equity, self.data, strategy)

    def plot(self):
        instruments = set([t.instrument for t in self.broker.closed_trades])
        for instrument in instruments:
            goog_data = self.data.get(instrument, Granularity.M1)
            trades = [
                trade
                for trade in self.broker.closed_trades
                if trade.instrument == instrument
            ]
            equity_df = pd.DataFrame(
                self.broker._equity, index=self.data._market_index, columns=["Equity"]
            )
            plot(goog_data, equity_df, trades)
