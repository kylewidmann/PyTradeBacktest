from typing import Any

import numpy as np
import pandas as pd
from pytrade.models.trade import Trade
from pytrade.strategy import FxStrategy

from pytradebacktest.data import MarketData


class Stats:

    def __init__(
        self,
        trades: list[Trade],
        equity: np.ndarray,
        market_data: MarketData,
        strategy: FxStrategy,
    ):
        self._trades = trades
        self._equity = equity
        self._market_data = market_data
        self._strategy = strategy
        self._trades_df = pd.DataFrame(
            {
                "Size": [t.size for t in trades],
                "EntryBar": [t.entry_bar for t in trades],
                "ExitBar": [t.exit_bar for t in trades],
                "EntryPrice": [t.entry_price for t in trades],
                "ExitPrice": [t.exit_price for t in trades],
                "PnL": [t.pl for t in trades],
                "ReturnPct": [t.pl_pct for t in trades],
                "EntryTime": [t.entry_time for t in trades],
                "ExitTime": [t.exit_time for t in trades],
                "Tag": [t.tag for t in trades],
                "TakeProfit": [t.tp for t in trades],
                "StopLoss": [t.sl for t in trades],
            }
        )
        self._trades_df["Duration"] = (
            self._trades_df["ExitTime"] - self._trades_df["EntryTime"]
        )
        self._drawdown: np.ndarray[np.floating[Any], Any]

    @property
    def drawdown(self) -> np.ndarray[np.floating[Any], Any]:
        if not self._drawdown:
            self._drawdown = 1 - self._equity / np.maximum.accumulate(self._equity)
        return self._drawdown

    @property
    def drawdown_duration(self):
        iloc = np.unique(
            np.r_[(self.drawdown == 0).values.nonzero()[0], len(self.drawdown) - 1]
        )
        iloc = pd.Series(iloc, index=self.drawdown.index[iloc])
        df = iloc.to_frame("iloc").assign(prev=iloc.shift())
        df = df[df["iloc"] > df["prev"] + 1].astype(int)

        # If no drawdown since no trade, avoid below for pandas sake and return nan series
        if not len(df):
            return (self.drawdown.replace(0, np.nan),) * 2

        # df = df.reindex(self.drawdown.index)
        return df["iloc"].map(self.drawdown.index.__getitem__) - df["prev"].map(
            self.drawdown.index.__getitem__
        )

    @property
    def drawdown_peaks(self):
        iloc = np.unique(
            np.r_[(self.drawdown == 0).values.nonzero()[0], len(self.drawdown) - 1]
        )
        iloc = pd.Series(iloc, index=self.drawdown.index[iloc])
        df = iloc.to_frame("iloc").assign(prev=iloc.shift())
        df = df[df["iloc"] > df["prev"] + 1].astype(int)

        # If no drawdown since no trade, avoid below for pandas sake and return nan series
        if not len(df):
            return (self.drawdown.replace(0, np.nan),) * 2

        # df = df.reindex(self.drawdown.index)
        return df.apply(
            lambda row: self.drawdown.iloc[row["prev"] : row["iloc"] + 1].max(), axis=1
        )

    @property
    def profit_and_loss(self):
        return self._trades_df["PnL"]

    @property
    def returns(self):
        return self._trades_df["ReturnPct"]

    @property
    def durations(self):
        return self._trades_df["Duration"]

    @property
    def start(self):
        return self._market_data._start_index
    
    @property
    def end(self):
        return self._market_data._end_index
    
    @property
    def duration(self):
        return self.start - self.end

    @property
    def positions(self):
        pass

    @property
    def exposure_time(self):
        pass

    @property
    def equity_final(self):
        pass

    @property
    def equity_peak(self):
        pass

    @property
    def return_pct(self):
        pass

    @property
    def buy_and_hold_return(self):
        pass

    @property
    def annualized_return(self):
        pass

    @property
    def annualized_volatility(self):
        pass

    @property
    def sharpe_ratio(self):
        pass

    @property
    def sortino_ratio(self):
        pass

    @property
    def calmar_ratio(self):
        pass

    @property
    def max_drawndown(self):
        pass

    @property
    def avg_drawdown(self):
        pass

    @property
    def max_drawdown_duration(self):
        pass

    @property
    def avg_drawdown_duration(self):
        pass

    @property
    def number_of_trades(self):
        pass

    @property
    def win_rate(self):
        pass

    @property
    def best_trade_return(self):
        pass

    @property
    def worst_trade_return(self):
        pass

    @property
    def avg_trade_return(self):
        pass

    @property
    def max_trade_duration(self):
        pass

    @property
    def avg_trade_duration(self):
        pass

    @property
    def profit_factor(self):
        pass

    @property
    def expectancy(self):
        pass

    @property
    def SQN(self):
        pass

    @property
    def kelly_criterion(self):
        pass
