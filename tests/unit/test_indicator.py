import numpy as np
from pytrade.models.indicator import Indicator

from pytradebacktest.data import MarketData


def test_indicator_values(data: np.ndarray, indicator: Indicator):
    assert len(indicator._values) == len(data)
    assert (indicator._values == data).all()


def test_indicator_updates(test_fx_universe: MarketData, indicator: Indicator):

    while test_fx_universe.next():
        pass
