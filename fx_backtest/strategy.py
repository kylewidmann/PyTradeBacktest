import asyncio
from typing import Type
from fx_lib.interfaces.broker import IBroker
from fx_lib.strategy import FxStrategy
from fx_lib.models.indicator import Indicator

from fx_backtest.data import BacktestCandleData, BacktestInstrumentCandles, MarketData

class BacktestStrategyWrapper:

    def __init__(self, broker: IBroker, data: MarketData, kstrategy: Type[FxStrategy]):
        self._data = data
        self._data_context = BacktestCandleData()
        self._strategy = kstrategy(broker, self._data_context)
        self._current_index = None

    def init(self):
        for key, df in self._data.universe.items():
            self._data_context.populate(df, key[0], key[1])

        self._strategy.init()

        self._indicators = {attr: indicator
                for attr, indicator in self._strategy.__dict__.items()
                if isinstance(indicator, Indicator)}.items()
        
        self._indicator_values = {attr: indicator._values for attr, indicator in self._indicators }

        self._indicator_i_index = {attr: None for attr, indicator in self._indicators}

    async def next(self) -> None:

        self._data_context.index = self._data.index
        indicator_updated = False

        # Incrememnt indicators
        for attr, indicator in self._indicators:
            if isinstance(indicator._data, BacktestInstrumentCandles):
                previous_i_index = self._indicator_i_index.get(attr)
                if previous_i_index != indicator._data.i_index:
                    indicator._values = self._indicator_values[attr][:indicator._data.i_index+1]
                    self._indicator_i_index[attr] = indicator._data.i_index
                    indicator_updated = True

        if indicator_updated:
            # Call _next directly so we don't wait for pending updates
            self._strategy._next()