import os
import pytest

from fx_backtest.utils import load_csv


@pytest.mark.parametrize(
        "path,count",
        [
            ("tests/unit/assets/EURGBP-2024-05_1Min.csv", 44460), 
            ("tests/unit/assets/EURJPY-2024-05_1Min.csv", 44460), 
            ("tests/unit/assets/EURUSD-2024-05_1Min.csv", 44460), 
            ("tests/unit/assets/GBPUSD-2024-05_1Min.csv", 44460)
        ]
)
def test_load_csvs(path, count):
    df = load_csv(path, parse_dates=["Timestamp"])
    assert df.shape[0] == count