from datetime import timezone

import pandas as pd
import pytest

from pytradebacktest.backtest import Backtest
from tests.unit.resources.indicators import SmaCross


@pytest.mark.asyncio
async def test_stats(test_stock_universe):
    test = Backtest(test_stock_universe, SmaCross, 10000)
    stats = await test.run()

    assert stats.total_trades == 66
    assert stats.avg_drawdown_duration == pd.Timedelta("41 days 00:00:00")
    assert stats.avg_drawdown == -5.925851581948801
    assert stats.avg_trade_duration == pd.Timedelta("46 days 00:00:00")
    assert stats.avg_trade_return == 2.531715975158555
    assert stats.best_trade_return == 53.59595229490424
    assert stats.calmar_ratio == 0.4414380935608377
    assert stats.duration == pd.Timedelta("3116 days 00:00:00")
    assert stats.end == pd.Timestamp("2013-03-01 00:00:00", tzinfo=timezone.utc)
    assert stats.equity_final == 51422.98999999996
    assert stats.equity_peak == 75787.44
    assert stats.expectancy == 3.274807806674883
    assert stats.exposure_time == 96.74115456238361
    assert stats.max_drawdown_duration == pd.Timedelta("584 days 00:00:00")
    assert stats.max_drawdown_pct == -47.98012705007589
    assert stats.max_trade_duration == pd.Timedelta("183 days 00:00:00")
    assert stats.profit_factor == 2.167945974262033
    assert stats.annualized_return_pct == 21.180255813792282
    assert stats.return_pct == 414.2298999999996
    assert stats.annualized_volatility == 36.49390889140787
    assert stats.SQN == 1.07661873566977
    assert stats.kelly_criterion == 0.1518705127029717
    assert stats.sharpe_ratio == 0.5803778344714113
    assert stats.start == pd.Timestamp("2004-08-19 00:00:00", tzinfo=timezone.utc)
    assert stats.win_rate == 46.96969696969697
    assert stats.worst_trade_return == -18.39887353835481
