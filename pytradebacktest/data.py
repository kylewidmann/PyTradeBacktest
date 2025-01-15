from abc import abstractmethod
from typing import Tuple

import numpy as np
import pandas as pd
from pandas import Timedelta, Timestamp
from pytrade.models.instruments import (
    CandleData,
    FxInstrument,
    Granularity,
    InstrumentCandles,
)

from pytradebacktest.utils import load_csv


class DataSource:

    def __init__(self, instrument: FxInstrument | str, granularity: Granularity):
        self.instrument = instrument
        self.granularity = granularity


class CsvDataSource(DataSource):

    def __init__(
        self, path: str, instrument: FxInstrument | str, granularity: Granularity
    ):
        super().__init__(instrument, granularity)
        self.path = path


class MarketDataLoader:

    @abstractmethod
    def load(self) -> dict[Tuple[FxInstrument | str, Granularity], pd.DataFrame]:
        raise NotImplementedError


class CsvMarketDataLoader(MarketDataLoader):

    def __init__(self, sources: list[CsvDataSource]):
        self.sources = sources

    def load(self) -> dict[Tuple[FxInstrument | str, Granularity], pd.DataFrame]:
        _sources = dict()

        for source in self.sources:
            df = load_csv(source.path, parse_dates=["Timestamp"])
            df = df.set_index("Timestamp")
            df.replace("", np.nan, inplace=True)
            df.dropna(inplace=True)
            _sources[(source.instrument, source.granularity)] = df

        return _sources


class MarketData:

    def __init__(self, loader: MarketDataLoader):
        self._sources = loader.load()
        self._init_index()

    @property
    def universe(self):
        return self._sources

    @property
    def index(self):
        return self._index

    def __len__(self):
        return len(self._market_index)

    def _init_index(self):
        _market_index = pd.Index([])
        for df in self._sources.values():
            _market_index = _market_index.union(df.index)
            self._next = self.__next()

        self._market_index = _market_index
        self._index = _market_index[0]

    def next(self):
        try:
            next(self._next)
            result = True
        except StopIteration:
            result = False
        
        return result

    def __next(self):

        for idx in self._market_index:
            self._index = idx
            yield True

        yield False


class BacktestInstrumentCandles(InstrumentCandles):

    def __init__(
        self, data: pd.DataFrame, instrument: FxInstrument, granularity: Granularity
    ):
        super().__init__(data, max_size=-1)
        self._index = self._data.index[0]
        self._i_index = 0

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, value: pd.Timestamp):
        if value in self._data.index:
            self._index = value

    @property
    def i_index(self):
        return self._data.index.get_loc(self._index)

    # def next(self):
    #     while self._i_index < len(self._data.index):
    #         yield self._data[self._i_index]
    #         self._i_index += 1


class BacktestCandleData(CandleData):

    def __init__(self):
        self._max_size = -1
        self._data: dict[
            tuple[FxInstrument, Granularity], BacktestInstrumentCandles
        ] = {}
        self._index = None

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "instance"):
            cls.instance = super().__new__(cls)
        # Need to handle case where instantiatied and different max size is provided
        return cls.instance

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, value: pd.Timestamp):
        self._index = value
        for candles in self._data.values():
            candles.index = self._index

    def populate(
        self, df: pd.DataFrame, instrument: FxInstrument, granularity: Granularity
    ):
        key = (instrument, granularity)
        instrument_candles: BacktestInstrumentCandles = self._data.get(
            key,
            BacktestInstrumentCandles(df, instrument, granularity),
        )
        self._data[key] = instrument_candles
