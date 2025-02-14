from datetime import datetime, timezone

from pytrade.instruments import FxInstrument, Granularity

from pytradebacktest.data import MarketData


def test_load_market_data(test_fx_universe):
    data = test_fx_universe
    assert len(data._sources) == 8


def test_init_index(test_fx_universe):
    data: MarketData = test_fx_universe

    assert data.index == datetime(2024, 5, 1, tzinfo=timezone.utc)


def test_fx_length(test_fx_universe):
    assert len(test_fx_universe) == 32940


def test_stock_length(test_stock_universe):
    assert len(test_stock_universe) == 2148


def test_preload_candles(test_fx_universe):
    data: MarketData = test_fx_universe

    assert data.i == 0
    assert data.index == datetime(2024, 5, 1, tzinfo=timezone.utc)

    data.load_instrument_candles(FxInstrument.EURUSD, Granularity.M1, 5)

    assert data.i == 5
    assert data.index == datetime(2024, 5, 1, 0, 5, tzinfo=timezone.utc)

    data.load_instrument_candles(FxInstrument.EURUSD, Granularity.M1, 10)

    assert data.i == 10
    assert data.index == datetime(2024, 5, 1, 0, 10, tzinfo=timezone.utc)

    data.load_instrument_candles(FxInstrument.EURUSD, Granularity.M1, 7)

    assert data.i == 10
    assert data.index == datetime(2024, 5, 1, 0, 10, tzinfo=timezone.utc)
