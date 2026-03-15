import numpy as np
from pytrade.indicator import Indicator
from pytrade.instruments import FxInstrument, Granularity

from pytradebacktest.data import MarketData


class OpenIndicator(Indicator):
    def _run(self, *args, **kwargs):
        return self._data.df.open


def test_indicator_values(data: np.ndarray, indicator: Indicator):
    assert len(indicator._values) == len(data)
    assert (indicator._values == data).all()


def test_indicator_updates(test_fx_universe: MarketData):
    def increment_indicator(self):
        if not hasattr(self, "_backtest_values"):
            self._backtest_values = self._values.copy()
        self._values = self._backtest_values[: len(self._data)]

    Indicator._update = increment_indicator

    data = test_fx_universe.get(FxInstrument.GBPUSD, Granularity.M1)
    indicator = OpenIndicator(data)

    data2 = test_fx_universe.get(FxInstrument.GBPUSD, Granularity.M5)
    indicator2 = OpenIndicator(data2)

    assert len(data) != len(data2)

    while test_fx_universe.next():
        assert len(indicator._values) == len(data)
        assert len(indicator2._values) == len(data2)
        assert data.index == test_fx_universe.index
        assert data2.index == test_fx_universe.index.floor(freq="5min")
