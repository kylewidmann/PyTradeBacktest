from numbers import Number
from typing import Sequence
from unittest.mock import patch
import pandas as pd
import pytest
from pytrade.interfaces.data import IInstrumentData
from pytrade.models.indicator import Indicator
from pytrade.models.instruments import CandleSubscription, FxInstrument, Granularity
from pytrade.strategy import FxStrategy

from pytradebacktest.backtest import Backtest

BACKTEST_INSTRUMENT = FxInstrument.EURUSD
BACKTEST_GRANULARITY = Granularity.M5


class BacktestIndicator(Indicator):

    def _run(self, *args, **kwargs):
        return self._data.Open > self._data.Close


class BacktestStrategy(FxStrategy):

    @property
    def subscriptions(self) -> list[CandleSubscription]:
        """
        Declare the `InstrumentSubscription`s this strategy should use
        for its signals
        """
        return [CandleSubscription(BACKTEST_INSTRUMENT, BACKTEST_GRANULARITY)]

    def _init(self) -> None:
        """
        Create indicators to be used for signals in the `_next` method.
        """
        data = self.get_data(BACKTEST_INSTRUMENT, BACKTEST_GRANULARITY)
        self.test_indicator = BacktestIndicator(data)

    def _next(self) -> None:
        """
        Evaluate indicators and submit orders to the broker
        """
        if self.test_indicator:
            self.sell(1)
        else:
            self.buy(1)

def SMA(arr: pd.Series, n: int) -> pd.Series:
    """
    Returns `n`-period simple moving average of array `arr`.
    """
    return pd.Series(arr).rolling(n).mean()

def crossover(series1: Sequence, series2: Sequence) -> bool:
    """
    Return `True` if `series1` just crossed over (above)
    `series2`.

        >>> crossover(self.data.Close, self.sma)
        True
    """
    series1 = (
        series1.values if isinstance(series1, pd.Series) else
        (series1, series1) if isinstance(series1, Number) else
        series1)
    series2 = (
        series2.values if isinstance(series2, pd.Series) else
        (series2, series2) if isinstance(series2, Number) else
        series2)
    try:
        return series1[-2] < series2[-2] and series1[-1] > series2[-1]
    except IndexError:
        return False
    
class Sma(Indicator):

    def __init__(self, data: IInstrumentData, period: int):
        self._period = period
        super().__init__(data)
        

    def _run(self):
        return pd.Series(self._data.Close).rolling(self._period).mean()


class SmaCross(FxStrategy):

    fast = 10
    slow = 30

    @property
    def subscriptions(self) -> list[CandleSubscription]:
        """
        Declare the `InstrumentSubscription`s this strategy should use
        for its signals
        """
        return [CandleSubscription("GOOG", Granularity.D1)]

    def _init(self) -> None:
        """
        Create indicators to be used for signals in the `_next` method.
        """
        data = self.get_data("GOOG", Granularity.D1)
        self.sma1 = Sma(data, self.fast)
        self.sma2 = Sma(data, self.slow)

    def _next(self):
        if crossover(self.sma1._values, self.sma2._values):
            # self.position.close()
            self.buy()
        elif crossover(self.sma2._values, self.sma1._values):
            # self.position.close()
            self.sell()


@patch("pytrade.strategy.FxStrategy.sell")
@patch("pytrade.strategy.FxStrategy.buy")
@pytest.mark.asyncio
async def test_backtest_trade_count(mock_buy, mock_sell, test_stock_universe):

    test = Backtest(test_stock_universe, SmaCross, 10000)
    await test.run()

    assert mock_buy.call_count + mock_sell.call_count == 66


