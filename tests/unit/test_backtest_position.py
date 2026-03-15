from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pandas as pd
import pytest
from pandas import Timestamp
from pytrade.models import Trade

from pytradebacktest.position import Position


def test_position():
    instrument_1 = "ABC"
    instrument_2 = "GOOG"

    entry_price = 98.90
    last_price = 105
    time1 = Timestamp(datetime.now())
    exit_price = 110.50
    time2 = time1 + timedelta(days=1, hours=2)
    goog_data = MagicMock()
    goog_data.last_price = last_price
    goog_df = pd.DataFrame({"Timestamp": [time1, time2], "Close": [entry_price, exit_price]})
    goog_df = goog_df.set_index("Timestamp")
    goog_data.df = goog_df

    abc_data = MagicMock()
    abc_data.last_price = last_price
    abc_df = pd.DataFrame({"Timestamp": [time1, time2], "Close": [entry_price, exit_price]})
    abc_df = abc_df.set_index("Timestamp")
    abc_data.df = abc_df

    abc_trades = [
        Trade(instrument_1, 100, 90, time1, abc_data),
        Trade(instrument_1, 150, 85, time2, abc_data),
    ]
    goog_trades = [
        Trade(instrument_2, 100, 90, time1, goog_data),
        Trade(instrument_2, 200, 100, time2, goog_data),
    ]
    trades = abc_trades + goog_trades

    position = Position(instrument_2, trades)

    assert len(position.trades) == 2
    assert position.size == 300
    assert position.pl == 2500
    trade1_pl_pct = (last_price / 90 - 1) * 100
    trade2_pl_pct = (last_price / 100 - 1) * 100
    position_pl_pct = 0.3333333333333333 * trade1_pl_pct + 0.6666666666666666 * trade2_pl_pct
    assert position.pl_pct == position_pl_pct
    assert position.is_long is True
    assert position.is_short is False


def test_position_close():
    instrument_1 = "ABC"
    instrument_2 = "GOOG"

    entry_price = 98.90
    last_price = 105
    time1 = Timestamp(datetime.now())
    exit_price = 110.50
    time2 = time1 + timedelta(days=1, hours=2)
    goog_data = MagicMock()
    goog_data.last_price = last_price
    goog_df = pd.DataFrame({"Timestamp": [time1, time2], "Close": [entry_price, exit_price]})
    goog_df = goog_df.set_index("Timestamp")
    goog_data.df = goog_df

    abc_data = MagicMock()
    abc_data.last_price = last_price
    abc_df = pd.DataFrame({"Timestamp": [time1, time2], "Close": [entry_price, exit_price]})
    abc_df = abc_df.set_index("Timestamp")
    abc_data.df = abc_df

    abc_trades = [
        Trade(instrument_1, 100, 90, time1, abc_data),
        Trade(instrument_1, 150, 85, time2, abc_data),
    ]
    trade_1 = Trade(instrument_2, 100, 90, time1, goog_data)
    trade_2 = Trade(instrument_2, 200, 100, time1, goog_data)
    goog_trades = [
        trade_1,
        trade_2,
    ]
    trades = abc_trades + goog_trades

    position = Position("GOOG", trades)

    trade_1.close(exit_price, time2)
    trade_2.close(exit_price, time2)

    assert position.size == 300
    assert position.pl == 4150
    assert position.pl_pct == pytest.approx(14.59, 1e-2)
