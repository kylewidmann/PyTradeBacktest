from unittest.mock import patch

import pandas as pd
import pytest
from pytrade.models.indicator import Indicator
from pytrade.models.instruments import CandleSubscription, Granularity, FxInstrument
from pytrade.strategy import FxStrategy

from pytradebacktest.broker import BacktestBroker
from pytradebacktest.data import MarketData
from pytradebacktest.strategy import BacktestStrategyWrapper

BACKTEST_INSTRUMENT = FxInstrument.EURUSD
BACKTEST_GRANULARITY = Granularity.M5


class BacktestIndicator(Indicator):

    def _run(self, *args, **kwargs):
        return self._data.Open > self._data.Close


class BacktestStrategy(FxStrategy):

    @property
    def subscriptions(self) -> list[CandleSubscription]:
        """
        Declare the `InstrumentSubscription`s this strategy should use
        for its signals
        """
        return [
            CandleSubscription(BACKTEST_INSTRUMENT, Granularity.M1),
            CandleSubscription(BACKTEST_INSTRUMENT, Granularity.M5),
        ]

    def _init(self) -> None:
        """
        Create indicators to be used for signals in the `_next` method.
        """
        self.eurusd_m1 = BacktestIndicator(
            self.get_data(BACKTEST_INSTRUMENT, Granularity.M1)
        )
        self.eurusd_m5 = BacktestIndicator(
            self.get_data(BACKTEST_INSTRUMENT, Granularity.M5)
        )

    def _next(self) -> None:
        """
        Evaluate indicators and submit orders to the broker
        """
        if self.eurusd_m5:
            self.sell(1)
        else:
            self.buy(1)


@pytest.mark.asyncio
async def test_strategy_indicator_updates(test_fx_universe: MarketData):

    broker = BacktestBroker(test_fx_universe)

    strategy = BacktestStrategyWrapper(broker, test_fx_universe, BacktestStrategy)
    strategy.init()

    m1_data: pd.DataFrame = test_fx_universe._sources.get(
        (BACKTEST_INSTRUMENT, Granularity.M1)
    )
    m5_data: pd.DataFrame = test_fx_universe._sources.get(
        (BACKTEST_INSTRUMENT, Granularity.M5)
    )
    indicator_data = {"eurusd_m1": m1_data, "eurusd_m5": m5_data}
    expected_indicator_values = {
        "eurusd_m1": m1_data.Open > m1_data.Close,
        "eurusd_m5": m5_data.Open > m5_data.Close,
    }

    for attr, indicator in strategy._indicators:
        assert len(indicator._values) == len(indicator_data[attr])

    while test_fx_universe.next():

        await strategy.next()
        for attr, indicator in strategy._indicators:
            if test_fx_universe.index in indicator._data.df.index:
                data_i_index = indicator._data.df.index.get_loc(test_fx_universe.index)
                expected_length = data_i_index + 1
                assert len(indicator._values) == expected_length
                assert indicator == expected_indicator_values[attr][data_i_index]


@patch("pytrade.strategy.FxStrategy.sell")
@patch("pytrade.strategy.FxStrategy.buy")
@pytest.mark.asyncio
async def test_strategy_indicator_orders(
    mock_buy, mock_sell, test_fx_universe: MarketData
):

    broker = BacktestBroker(test_fx_universe)

    strategy = BacktestStrategyWrapper(broker, test_fx_universe, BacktestStrategy)
    strategy.init()

    test_data: pd.DataFrame = test_fx_universe._sources.get(
        (BACKTEST_INSTRUMENT, BACKTEST_GRANULARITY)
    )

    while test_fx_universe.next():
        await strategy.next()

    expected_buy_calls = test_data[test_data.Open <= test_data.Close].count().Open
    expected_sell_calls = test_data[test_data.Open > test_data.Close].count().Open
    assert expected_buy_calls + expected_sell_calls == test_data.count().Open

    assert mock_buy.call_count == expected_buy_calls
    assert mock_sell.call_count == expected_sell_calls
