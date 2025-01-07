import pytest
from pytrade.models.indicator import Indicator
from pytrade.models.instruments import CandleSubscription, Granularity, Instrument
from pytrade.strategy import FxStrategy

from pytradebacktest.backtest import Backtest

BACKTEST_INSTRUMENT = Instrument.EURUSD
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


@pytest.mark.asyncio
async def test_backtest_increments_indicator(test_universe):

    test = Backtest(test_universe, BacktestStrategy, 10000)
    await test.run()
