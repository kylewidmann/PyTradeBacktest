from typing import Type

from pytrade.interfaces.broker import IBroker
from pytrade.models.indicator import Indicator
from pytrade.strategy import FxStrategy

from pytradebacktest.data import (
    BacktestCandleData,
    BacktestInstrumentCandles,
    MarketData,
)


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

        self._indicators = {
            attr: indicator
            for attr, indicator in self._strategy.__dict__.items()
            if isinstance(indicator, Indicator)
        }.items()

        self._indicator_values = {
            attr: indicator._values for attr, indicator in self._indicators
        }

        self._indicator_i_index = {attr: None for attr, indicator in self._indicators}

    async def next(self) -> None:

        self._data_context.index = self._data.index

        updates = []
        # Incrememnt indicators
        for attr, indicator in self._indicators:
            indicator_updated = False
            if isinstance(indicator._data, BacktestInstrumentCandles):
                previous_i_index = self._indicator_i_index.get(attr)
                if previous_i_index != indicator._data.i_index:
                    indicator._values = self._indicator_values[attr][
                        : indicator._data.i_index + 1
                    ]
                    self._indicator_i_index[attr] = indicator._data.i_index
                    indicator_updated = True

            updates.append(indicator_updated)

        all_updates_received = all(updates)

        # Currently making sure all indicators have been updated before calling next
        # This aligns with the pending update logic when the strategy is event
        # driven in live trading.  If that behavior changes this will also need to
        # change.
        if all_updates_received:
            # Call _next directly so we don't wait for pending updates
            self._strategy._next()
