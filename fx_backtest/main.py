import pandas as pd
from backtesting import Backtest
from fx_strategy.strategy import SlopeMomentum


def calculate_stop_loss(cash, pair, price, risk=0.01):
    pass


with open("/home/kyle/Tick_Data/ohlc/2024/January/GBPUSD-2024-01_5Min.csv") as fh:
    data = pd.read_csv(fh, parse_dates=["Timestamp"])
    data.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close"}, inplace=True)
    data = data.dropna()

bt = Backtest(
    data, SlopeMomentum, commission=0.000, exclusive_orders=False, margin=0.02
)

stats = bt.run()
bt.plot()
print(stats)
