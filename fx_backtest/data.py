from abc import abstractmethod
from typing import Optional, Tuple

import numpy as np
import pandas as pd
from fx_lib.events.event import Event
from pandas import Timestamp
from pandas import Timedelta
from fx_backtest.utils import load_csv
from fx_lib.models.instruments import CandleData, Instrument, InstrumentCandles, INDEX, COLUMNS
from fx_lib.models.instruments import Granularity

class DataSource:

    def __init__(self, instrument: Instrument, granularity: Granularity):
        self.instrument = instrument
        self.granularity = granularity

class CsvDataSource(DataSource):

    def __init__(self, path: str, instrument: Instrument, granularity: Granularity):
        super().__init__(instrument, granularity)
        self.path = path

class MarketDataLoader:

    @abstractmethod
    def load(self) -> dict[Tuple[Instrument, Granularity], pd.DataFrame]:
        raise NotImplementedError

class CsvMarketDataLoader(MarketDataLoader):

    def __init__(self, sources: list[CsvDataSource]):
        self.sources = sources

    def load(self) -> dict[Tuple[Instrument, Granularity], pd.DataFrame]:
        _sources = dict()

        for source in self.sources:
            df = load_csv(source.path, parse_dates=["Timestamp"])
            df = df.set_index("Timestamp")
            df.replace('', np.nan, inplace=True)
            df.dropna(inplace=True)
            _sources[(source.instrument, source.granularity)] = df

        return _sources

class MarketData:

    def __init__(self, loader: MarketDataLoader):
        self._sources = loader.load()
        # self._candle_events: dict[Tuple[Instrument, Granularity], CandlestickEvent] = {}
        self._init_timeframe()

    @property
    def universe(self):
        return self._sources
    
    @property
    def index(self):
        return self._index
    
    def _init_timeframe(self):
        _start = None
        _granularity = None
        _end = None
        for df in self._sources.values():
            start = df.index[0]
            end = df.index[-1]
            granularity = df.index[1] - df.index[0]

            if start:
                if not _start:
                    _start = start
                elif start < _start:
                    _start = start

            if end:
                if not _end:
                    _end = end
                elif end > _end:
                    _end = end

            if granularity:
                if not _granularity:
                    _granularity = granularity
                elif granularity < _granularity:
                    _granularity = granularity

        if not _start:
            raise RuntimeError("Unable to determine start time for market data.")
        
        if not _granularity:
            raise RuntimeError("Unable to determine smallest granularity for market data.")
        
        if not _end:
            raise RuntimeError("Unable to determine end time for market data.")
        
        self._index: Timestamp = _start - _granularity
        self._granularity: Timedelta  = _granularity
        self._end_index: Timestamp = _end

    def next(self):
        
        self._index = self._index + self._granularity
        return self._index <= self._end_index

class BacktestInstrumentCandles(InstrumentCandles):

    def __init__(
        self, data: pd.DataFrame, instrument: Instrument, granularity: Granularity
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
        self._data: dict[tuple[Instrument, Granularity], BacktestInstrumentCandles] = {}
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

    def populate(self, df: pd.DataFrame, instrument: Instrument, granularity: Granularity):
        key = (instrument, granularity)
        instrument_candles: BacktestInstrumentCandles = self._data.get(
            key,
            BacktestInstrumentCandles(df, instrument, granularity),
        )
        self._data[key] = instrument_candles