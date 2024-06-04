import pandas as pd
from backtesting import Backtest
from fx_strategy.strategy import SlopeMomentum


def calculate_stop_loss(cash, pair, price, risk=0.01):
    pass


with open("/home/kyle/Downloads/GBPUSD_M5.csv") as fh:
    data = pd.read_csv(fh, delimiter="\t", parse_dates=["Time"])

bt = Backtest(
    data, SlopeMomentum, commission=0.000, exclusive_orders=False, margin=0.02
)

stats = bt.run()
bt.plot()
print(stats)
