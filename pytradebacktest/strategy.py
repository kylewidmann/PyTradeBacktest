from typing import Type

from pytrade.indicator import Indicator
from pytrade.interfaces.broker import IBroker
from pytrade.strategy import FxStrategy

from pytradebacktest.data import (
    InstrumentData,
    MarketData,
)


class BacktestStrategyWrapper:

    def __init__(self, broker: IBroker, data: MarketData, kstrategy: Type[FxStrategy]):
        self._data = data
        self._strategy = kstrategy(broker, data)
        self._current_index = None

    def init(self):

        self._strategy.init()

        self._indicators = {
            attr: indicator
            for attr, indicator in self._strategy.__dict__.items()
            if isinstance(indicator, Indicator)
        }.items()

        # Monkey patch indicators so their update does not
        # need to recalculate after each increment, instead
        # store their initial values from the full data context
        # and then increment based on the current context length
        def increment_indicator(self):
            if not hasattr(self, "_backtest_values"):
                self._backtest_values = self._values.copy()
            self._values = self._backtest_values[: len(self._data)]

        Indicator._update = increment_indicator


    # async def next(self) -> None:

        # updates = []
        # # Incrememnt indicators
        # for attr, indicator in self._indicators:
        #     indicator_updated = False
        #     if isinstance(indicator._data, InstrumentData):
        #         previous_i_index = self._indicator_i_index.get(attr)
        #         if previous_i_index != indicator._data.i_index:
        #             indicator._values = self._indicator_values[attr][
        #                 : indicator._data.i_index + 1
        #             ]
        #             self._indicator_i_index[attr] = indicator._data.i_index
        #             indicator_updated = True

        #     updates.append(indicator_updated)

        # all_updates_received = all(updates)

        # # Currently making sure all indicators have been updated before calling next
        # # This aligns with the pending update logic when the strategy is event
        # # driven in live trading.  If that behavior changes this will also need to
        # # change.
        # if all_updates_received:
        #     # Call _next directly so we don't wait for pending updates
        #     self._strategy._next()
