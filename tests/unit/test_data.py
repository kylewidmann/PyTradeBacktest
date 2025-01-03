from datetime import datetime
from datetime import timedelta

from fx_backtest.data import CsvDataSource, CsvMarketDataLoader, MarketData
from fx_lib.models.instruments import Instrument, Granularity, Candlestick

def test_load_market_data(test_universe):
    data = test_universe
    assert len(data._sources) == 8

def test_init_timeframe(test_universe):
    data = test_universe

    assert data._index == datetime(2024, 5, 1)
    assert data._granularity == timedelta(minutes=1)

def test_updates(test_universe):
    data: MarketData = test_universe

    sources_count = len(data._sources)

    _candles = []
    def _handle_update(candle: Candlestick):
        _candles.append(candle)

    for instrument, granularity in data._sources.keys():
        data.subscribe(instrument, granularity, _handle_update)

    for i in range(10):
        data.next()

        assert len(_candles) == sources_count * (i + 1)