from datetime import datetime, timedelta

from pytradebacktest.data import MarketData


def test_load_market_data(test_fx_universe):
    data = test_fx_universe
    assert len(data._sources) == 8


def test_init_timeframe(test_fx_universe):
    data: MarketData = test_fx_universe

    assert data._index == datetime(2024, 4, 30, 23, 59)
    assert data._granularity == timedelta(minutes=1)


def test_fx_length(test_fx_universe):
    assert len(test_fx_universe) == 44459


def test_stock_length(test_stock_universe):
    assert len(test_stock_universe) == 3116
