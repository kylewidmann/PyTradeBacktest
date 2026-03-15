from numbers import Number
from typing import Union

import numpy as np
import pandas as pd
from pandas import DatetimeIndex
from pytrade.models import Trade
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
        self._index: DatetimeIndex = market_data._market_index
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
        self._trades_df["Duration"] = self._trades_df["ExitTime"] - self._trades_df["EntryTime"]

        self._compute_drawdown_stats()

        self._equity_df = pd.DataFrame(
            {
                "Equity": equity,
                "DrawdownPct": self.drawdown,
                "DrawdownDuration": self.drawdown_duration,
            },
            index=self._market_data._market_index,
        )
        self._risk_free_rate = 0

    def __repr__(self):
        return f"""
# Trades: {self.number_of_trades},
Avg. Drawdown Duration: {self.avg_drawdown_duration},
Avg. Drawdown [%]: {self.avg_drawdown},
Avg. Trade Duration: {self.avg_trade_duration},
Avg. Trade [%]: {self.avg_trade_return},
Best Trade [%]: {self.best_trade_return},
Calmar Ratio: {self.calmar_ratio},
Duration: {self.duration},
End: {self.end},
Equity Final [$]: {self.equity_final},
Equity Peak [$]: {self.equity_peak},
Expectancy [%]: {self.expectancy},
Exposure Time [%]: {self.exposure_time},
Max. Drawdown Duration: {self.max_drawdown_duration},
Max. Drawdown [%]: {self.max_drawdown_pct},
Max. Trade Duration: {self.max_trade_duration},
Profit Factor: {self.profit_factor},
Return (Ann.) [%]: {self.annualized_return_pct},
Return [%]: {self.return_pct},
Volatility (Ann.) [%]: {self.annualized_volatility},
SQN: {self.SQN},
Kelly Criterion: {self.kelly_criterion},
Sharpe Ratio: {self.sharpe_ratio},
Sortino Ratio: {self.sortino_ratio},
Start: {self.start},
Win Rate [%]: {self.win_rate},
Worst Trade [%]: {self.worst_trade_return},
"""

    @property
    def total_trades(self):
        return len(self._trades_df)

    @property
    def drawdown(self) -> pd.Series:
        return self._drawdown

    @property
    def drawdown_duration(self):
        return self._drawdown_duration

    @property
    def drawdown_peaks(self):
        return self._drawdown_peaks

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
        return self._index[0]

    @property
    def end(self):
        return self._index[-1]

    @property
    def duration(self):
        return self.end - self.start

    @property
    def positions(self):
        pass

    @property
    def exposure_time(self):
        have_position = np.repeat(0, len(self._index))
        for t in self._trades_df.itertuples(index=False):
            have_position[t.EntryBar : t.ExitBar + 1] = 1

        return have_position.mean() * 100

    @property
    def equity_final(self):
        return self._equity[-1]

    @property
    def equity_peak(self):
        return self._equity.max()

    @property
    def return_pct(self):
        equity = self._equity
        return (equity[-1] - equity[0]) / equity[0] * 100

    @property
    def annualized_return(self):
        day_returns = self._equity_df["Equity"].resample("D").last().dropna().pct_change()
        gmean_day_return = self._geometric_mean(day_returns)
        annual_trading_days = float(
            365 if self._index.dayofweek.to_series().between(5, 6).mean() > 2 / 7 * 0.6 else 252
        )
        return (1 + gmean_day_return) ** annual_trading_days - 1

    @property
    def annualized_return_pct(self):
        return self.annualized_return * 100

    @property
    def annualized_volatility(self):
        day_returns = self._equity_df["Equity"].resample("D").last().dropna().pct_change()
        gmean_day_return = self._geometric_mean(day_returns)
        annual_trading_days = float(
            365 if self._index.dayofweek.to_series().between(5, 6).mean() > 2 / 7 * 0.6 else 252
        )
        return (
            np.sqrt(
                (day_returns.var(ddof=int(bool(day_returns.shape))) + (1 + gmean_day_return) ** 2)
                ** annual_trading_days
                - (1 + gmean_day_return) ** (2 * annual_trading_days)
            )
            * 100
        )

    @property
    def sharpe_ratio(self):
        return (self.annualized_return_pct - self._risk_free_rate * 100) / (
            self.annualized_volatility or np.nan
        )

    @property
    def sortino_ratio(self):
        day_returns = self._equity_df["Equity"].resample("D").last().dropna().pct_change()
        annualized_return = self.annualized_return
        annual_trading_days = float(
            365 if self._index.dayofweek.to_series().between(5, 6).mean() > 2 / 7 * 0.6 else 252
        )
        return (annualized_return - self._risk_free_rate) / (
            np.sqrt(np.mean(day_returns.clip(-np.inf, 0) ** 2)) * np.sqrt(annual_trading_days)
        )  # noqa: E501

    @property
    def calmar_ratio(self):
        return self.annualized_return / (-self.max_drawndown or np.nan)

    @property
    def max_drawndown(self):
        return -np.nan_to_num(self.drawdown.max())

    @property
    def max_drawdown_pct(self):
        return self.max_drawndown * 100

    @property
    def avg_drawdown(self):
        return -self.drawdown_peaks.mean() * 100

    @property
    def max_drawdown_duration(self):
        return self._round_timedelta(self.drawdown_duration.max())

    @property
    def avg_drawdown_duration(self):
        return self._round_timedelta(self.drawdown_duration.mean())

    @property
    def number_of_trades(self):
        return len(self._trades_df)

    @property
    def win_rate(self):
        return (np.nan if not self.number_of_trades else (self.profit_and_loss > 0).mean()) * 100

    @property
    def best_trade_return(self):
        return self.returns.max()

    @property
    def worst_trade_return(self):
        return self.returns.min()

    @property
    def avg_trade_return(self):
        return self._geometric_mean(self.returns / 100) * 100

    @property
    def max_trade_duration(self):
        return self._round_timedelta(self.durations.max())

    @property
    def avg_trade_duration(self):
        return self._round_timedelta(self.durations.mean())

    @property
    def profit_factor(self):
        returns = self.returns
        return returns[returns > 0].sum() / (abs(returns[returns < 0].sum()) or np.nan)

    @property
    def expectancy(self):
        return self.returns.mean()

    @property
    def SQN(self):
        n_trades = self.number_of_trades
        pl = self.profit_and_loss
        return np.sqrt(n_trades) * pl.mean() / (pl.std() or np.nan)

    @property
    def kelly_criterion(self):
        pl = self.profit_and_loss
        win_rate = np.nan if not len(self._trades_df) else (pl > 0).mean()
        return win_rate - (1 - win_rate) / (pl[pl > 0].mean() / -pl[pl < 0].mean())

    def _compute_drawdown_stats(self):
        _drawdown = 1 - self._equity / np.maximum.accumulate(self._equity)
        self._drawdown = pd.Series(_drawdown, index=self._index)

        iloc = np.unique(np.r_[(self._drawdown == 0).values.nonzero()[0], len(self._drawdown) - 1])
        iloc = pd.Series(iloc, index=self._drawdown.index[iloc])
        df = iloc.to_frame("iloc").assign(prev=iloc.shift())
        df = df[df["iloc"] > df["prev"] + 1].astype(int)

        # If no drawdown since no trade, avoid below for pandas sake and return nan series
        if not len(df):
            self._drawdown_duration, self._drawdown_peaks = (self._drawdown.replace(0, np.nan),) * 2
        else:
            df["duration"] = df["iloc"].map(self._drawdown.index.__getitem__) - df["prev"].map(
                self.drawdown.index.__getitem__
            )

            df["peak_dd"] = df.apply(
                lambda row: self._drawdown.iloc[row["prev"] : row["iloc"] + 1].max(),
                axis=1,
            )

            df = df.reindex(self.drawdown.index)

            self._drawdown_duration, self._drawdown_peaks = (
                df["duration"],
                df["peak_dd"],
            )

    def _data_period(self, index) -> Union[pd.Timedelta, Number]:
        """Return data index period as pd.Timedelta"""
        values = pd.Series(index[-100:])
        return values.diff().dropna().median()

    def _round_timedelta(self, value):
        if not isinstance(value, pd.Timedelta):
            return value

        _period = self._data_period(self._index)
        resolution = getattr(_period, "resolution_string", None) or _period.resolution
        return value.ceil(resolution)

    def _geometric_mean(self, returns: pd.Series) -> float:
        returns = returns.fillna(0) + 1
        if np.any(returns <= 0):
            return 0
        return np.exp(np.log(returns).sum() / (len(returns) or np.nan)) - 1
