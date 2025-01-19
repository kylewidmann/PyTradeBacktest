from unittest.mock import patch

import pytest

from pytradebacktest.backtest import Backtest
from tests.unit.fixtures import SmaCross


@patch("pytradebacktest.backtest.BacktestBroker.order")
@pytest.mark.asyncio
async def test_backtest_trade_count(mock_order, test_stock_universe):

    test = Backtest(test_stock_universe, SmaCross, 10000)
    await test.run()

    assert mock_order.call_count == 66