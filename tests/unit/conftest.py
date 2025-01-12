import numpy as np
import pandas as pd
import pytest
from pytrade.events.event import Event
from pytrade.models.indicator import Indicator
from pytrade.models.instruments import Granularity, IInstrumentData, FxInstrument

from pytradebacktest.data import CsvDataSource, CsvMarketDataLoader, MarketData


class TestIndicator(Indicator):

    def _run(self, *args, **kwargs):
        return self._data.df.values.flatten()


class TestData(IInstrumentData):

    def __init__(self, data: pd.DataFrame):
        self._data = data
        self.__update_event = Event()

    @property
    def df(self):
        return self._data

    @property
    def on_update(self):
        return self.__update_event

    @on_update.setter
    def on_update(self, value: Event):
        self.__update_event = value


@pytest.fixture(scope="module")
def data():
    return np.array([1, 2, 3, 4, 5])


@pytest.fixture(scope="module")
def instrument_data(data):
    df = pd.DataFrame(data)
    return TestData(df)


@pytest.fixture(scope="module")
def indicator(instrument_data):
    return TestIndicator(instrument_data)


@pytest.fixture(scope="module")
def test_csv_sources() -> list[CsvDataSource]:
    return [
        CsvDataSource(
            "tests/unit/assets/EURGBP-2024-05_1Min.csv",
            FxInstrument.EURGBP,
            Granularity.M1,
        ),
        CsvDataSource(
            "tests/unit/assets/EURJPY-2024-05_1Min.csv",
            FxInstrument.EURJPY,
            Granularity.M1,
        ),
        CsvDataSource(
            "tests/unit/assets/EURUSD-2024-05_1Min.csv",
            FxInstrument.EURUSD,
            Granularity.M1,
        ),
        CsvDataSource(
            "tests/unit/assets/GBPUSD-2024-05_1Min.csv",
            FxInstrument.GBPUSD,
            Granularity.M1,
        ),
        CsvDataSource(
            "tests/unit/assets/EURGBP-2024-05_5Min.csv",
            FxInstrument.EURGBP,
            Granularity.M5,
        ),
        CsvDataSource(
            "tests/unit/assets/EURJPY-2024-05_5Min.csv",
            FxInstrument.EURJPY,
            Granularity.M5,
        ),
        CsvDataSource(
            "tests/unit/assets/EURUSD-2024-05_5Min.csv",
            FxInstrument.EURUSD,
            Granularity.M5,
        ),
        CsvDataSource(
            "tests/unit/assets/GBPUSD-2024-05_5Min.csv",
            FxInstrument.GBPUSD,
            Granularity.M5,
        ),
    ]

@pytest.fixture(scope="module")
def test_stock_sources() -> list[CsvDataSource]:
    return [
        CsvDataSource(
            "tests/unit/assets/GOOG.csv",
            "GOOG",
            Granularity.D1,
        )
    ]


@pytest.fixture(scope="function")
def test_fx_universe(test_csv_sources):
    return MarketData(CsvMarketDataLoader(test_csv_sources))

@pytest.fixture(scope="function")
def test_stock_universe(test_stock_sources):
    return MarketData(CsvMarketDataLoader(test_stock_sources))
