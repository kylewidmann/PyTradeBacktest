from datetime import datetime
from pytradebacktest.data import MarketData


def test_load_market_data(test_fx_universe):
    data = test_fx_universe
    assert len(data._sources) == 8


def test_init_index(test_fx_universe):
    data: MarketData = test_fx_universe

    assert data._index == datetime(2024, 5, 1)


def test_fx_length(test_fx_universe):
    assert len(test_fx_universe) == 32930


def test_stock_length(test_stock_universe):
    assert len(test_stock_universe) == 2148
