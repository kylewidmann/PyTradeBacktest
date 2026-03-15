from unittest.mock import ANY, MagicMock, patch

import pytest

from pytradebacktest.backtest import Backtest
from tests.unit.resources.indicators import SmaCross


@patch("pytradebacktest.backtest.BacktestBroker.order")
@pytest.mark.asyncio
async def test_backtest_trade_count(mock_order, test_stock_universe):
    test = Backtest(test_stock_universe, SmaCross, 10000)
    await test.run()

    assert mock_order.call_count == 66


@patch("tests.unit.resources.indicators.SmaCross")
@pytest.mark.asyncio
async def test_strategy_kwargs(mock_strategy, test_stock_universe):
    mock_instance = MagicMock()
    mock_strategy.return_value = mock_instance

    test = Backtest(test_stock_universe, mock_strategy, 10000)
    await test.run(arg1="test1", arg2="test2")

    mock_strategy.assert_called_with(ANY, ANY, arg1="test1", arg2="test2")
