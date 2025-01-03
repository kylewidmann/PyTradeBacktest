import pandas as pd
from fx_strategy.strategy import SlopeMomentum
from fx_lib.models.instruments import Instrument, Granularity

from fx_backtest.backtest import Backtest
from fx_backtest.data import CsvDataSource, CsvMarketDataLoader, MarketData

test_universe = MarketData(CsvMarketDataLoader([
    CsvDataSource("/home/kyle/Tick_Data/ohlc/2024/February/EURUSD-2024-02_5Min.csv", Instrument.EURUSD, Granularity.M5)
]))
bt = Backtest(
    test_universe, SlopeMomentum, 10000, margin=0.02
)

stats = bt.run()
bt.plot()
print(stats)
