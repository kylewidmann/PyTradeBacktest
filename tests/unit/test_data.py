from datetime import datetime, timedelta

from pytradebacktest.data import MarketData


def test_load_market_data(test_universe):
    data = test_universe
    assert len(data._sources) == 8


def test_init_timeframe(test_universe):
    data: MarketData = test_universe

    assert data._index == datetime(2024, 4, 30, 23, 59)
    assert data._granularity == timedelta(minutes=1)


# def test_updates(test_universe):
#     data: MarketData = test_universe

#     sources_count = len(data._sources)

#     _candles = []

#     def _handle_update(candle: Candlestick):
#         _candles.append(candle)

#     for instrument, granularity in data._sources.keys():
#         data.subscribe(instrument, granularity, _handle_update)

#     for i in range(10):
#         data.next()

#         assert len(_candles) == sources_count * (i + 1)
