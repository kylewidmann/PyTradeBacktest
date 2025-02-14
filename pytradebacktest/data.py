from abc import abstractmethod
from datetime import timezone
from typing import Optional

import numpy as np
import pandas as pd
from pandas import DatetimeIndex, Timestamp
from pytrade.events.event import Event
from pytrade.instruments import Granularity, Instrument
from pytrade.interfaces.data import IDataContext, IInstrumentData

from pytradebacktest.utils import load_csv


class InstrumentData(IInstrumentData):

    def __init__(
        self, instrument: Instrument, granularity: Granularity, df: pd.DataFrame
    ):
        self.__df = df
        self.__i = len(df) - 1
        self.__pip: Optional[float] = None
        self._instrument = instrument
        self._granularity = granularity
        self._update_event = Event()

    def __len__(self):
        return self.__i + 1

    @property
    def instrument(self) -> Instrument:
        return self._instrument

    @property
    def granularity(self) -> Granularity:
        return self._granularity

    @property
    def df(self) -> pd.DataFrame:
        return (
            self.__df.iloc[: self.__i + 1] if self.__i < len(self.__df) else self.__df
        )

    @property
    def on_update(self) -> Event:
        return self._update_event

    @on_update.setter
    def on_update(self, value: Event):
        self._update_event = value

    @property
    def timestamp(self):
        return self.index

    @property
    def prev_timestamp(self):
        return self.__df.index[self.__i - 1]

    @property
    def i_index(self):
        return self.__i

    @property
    def index(self) -> Timestamp:
        return self.__df.index[self.__i]

    @index.setter
    def index(self, value: Timestamp):
        if value in self.__df.index:
            self.__i = self.__df.index.get_loc(value)  # type: ignore

            self._update_event()


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
    def load(self) -> list[InstrumentData]:
        raise NotImplementedError


class CsvMarketDataLoader(MarketDataLoader):

    def __init__(self, sources: list[CsvDataSource]):
        self.sources = sources

    def load(self) -> list[InstrumentData]:
        _sources = []

        for source in self.sources:
            df = load_csv(source.path, parse_dates=["datetime"])
            df = df.set_index("datetime")
            df.replace("", np.nan, inplace=True)
            df.dropna(inplace=True)
            index: DatetimeIndex = pd.to_datetime(df.index)
            df.index = index.tz_localize(tz=timezone.utc)
            instrument_data = InstrumentData(source.instrument, source.granularity, df)
            _sources.append(instrument_data)

        return _sources


class MarketData(IDataContext):

    def __init__(self, loader: MarketDataLoader):
        self._sources = loader.load()
        self._init_index()

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "instance"):
            cls.instance = super().__new__(cls)
        # Need to handle case where instantiatied and different max size is provided
        return cls.instance

    @property
    def universe(self):
        return self._sources

    @property
    def index(self):
        return self._index

    @property
    def i(self) -> int:
        return self._market_index.get_loc(self._index)

    def __len__(self):
        return len(self._market_index)

    def _init_index(self):
        _market_index: DatetimeIndex = DatetimeIndex([])
        for source in self._sources:
            _market_index = _market_index.union(source.df.index)

        _market_index = pd.to_datetime(_market_index)

        self._next = self.__next()
        self._market_index = _market_index
        self._index = _market_index[0]

    def next(self):
        try:
            result = next(self._next)
        except StopIteration:
            result = False

        return result

    def __next(self):

        for idx in self._market_index:
            self._index = idx
            for source in self._sources:
                source.index = idx
            yield True

        yield False

    def get(self, instrument: Instrument, granularity: Granularity) -> IInstrumentData:
        return next(
            src
            for src in self._sources
            if src.instrument == instrument and src.granularity == granularity
        )
