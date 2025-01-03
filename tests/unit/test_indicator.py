from fx_lib.models.indicator import Indicator
import numpy as np

from fx_backtest.data import MarketData

def test_indicator_values(data: np.ndarray, indicator: Indicator):
    assert len(indicator._values) == len(data)
    assert (indicator._values == data).all()


def test_indicator_updates(test_universe: MarketData, indicator: Indicator):
    data_c
    while test_universe.next():
        pass