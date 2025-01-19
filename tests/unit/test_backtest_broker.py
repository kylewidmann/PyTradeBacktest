from pytrade.models.order import OrderRequest

from pytradebacktest.broker import BacktestBroker


def test_fill_stock_order(test_stock_universe):

    broker = BacktestBroker(test_stock_universe, 10000, 0, 1, False, False, False)

    broker.order(OrderRequest("GOOG", 100))

    broker.next()
