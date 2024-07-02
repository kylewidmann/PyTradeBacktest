import pandas as pd
from fx_strategy.strategy import SlopeMomentum

from fx_backtest.backtesting import Backtest, BacktestStrategy

with open("/home/kyle/Tick_Data/ohlc/2024/February/EURUSD-2024-02_5Min.csv") as fh:
    data = pd.read_csv(fh, parse_dates=["Timestamp"])
    data.rename(
        columns={"open": "Open", "high": "High", "low": "Low", "close": "Close"},
        inplace=True,
    )
    data = data.dropna()

bt = Backtest(
    data, BacktestStrategy, commission=0.000, exclusive_orders=False, margin=0.02
)

stats = bt.run(_klass=SlopeMomentum)
bt.plot()
print(stats)
