import pytest
from pytrade.broker import Order
from pytrade.instruments import Granularity

from pytradebacktest.broker import BacktestBroker
from pytradebacktest.data import MarketData
from pytradebacktest.exceptions import OutOfMoneyError


@pytest.mark.parametrize("iterations", [1, 10, 50, 75, 100])
def test_fill_market_order(iterations, test_stock_universe: MarketData):
    goog_data = test_stock_universe.get("GOOG", Granularity.D1).df.copy()
    broker = BacktestBroker(test_stock_universe, 100000, 0, 1, False, False, False)

    for _ in range(iterations):
        test_stock_universe.next()

    broker.order(Order("GOOG", 100))

    broker.next()

    assert len(broker.orders) == 0
    assert len(broker.trades) == 1
    trade = broker.trades[0]
    assert trade.entry_price == goog_data.open.iloc[iterations - 1]


def test_market_order_not_enough_equity(test_stock_universe: MarketData):
    broker = BacktestBroker(test_stock_universe, 100, 0, 1, False, False, False)

    test_stock_universe.next()
    broker.order(Order("GOOG", 1000))
    broker.next()

    assert len(broker.orders) == 0
    assert len(broker.trades) == 0


@pytest.mark.parametrize("price_index", [1, 10, 50, 75, 100])
@pytest.mark.parametrize("buy", [True, False])
def test_stop_order_conversion(price_index, buy, test_stock_universe: MarketData):
    goog_data = test_stock_universe.get("GOOG", Granularity.D1).df.copy()
    broker = BacktestBroker(test_stock_universe, 100000, 0, 1, False, False, False)

    price_timestamp = (
        goog_data[:price_index].high.idxmax() if buy else goog_data[:price_index].low.idxmin()
    )
    price_idx = goog_data.index.get_loc(price_timestamp)
    price = goog_data.high.iloc[price_idx] if buy else goog_data.low.iloc[price_idx]
    stop = price - 0.01 if buy else price + 0.01  # Set to 1 cent past price
    size = 100 if buy else -100
    broker.order(Order("GOOG", size, stop=stop))

    for i in range(price_idx):
        test_stock_universe.next()
        assert len(broker.orders) == 1
        assert len(broker.trades) == 0
        assert broker.orders[0].stop == stop
        broker.next()

    # Perform one more iteration
    test_stock_universe.next()
    broker.next()

    # Should have executed on the next iteration
    assert len(broker.orders) == 0
    assert len(broker.trades) == 1
    trade = broker.trades[0]
    assert trade.entry_price == stop


@pytest.mark.parametrize("price_index", [1, 10, 50, 75, 100])
@pytest.mark.parametrize("buy", [True, False])
def test_limit_order_conversion(price_index, buy, test_stock_universe: MarketData):
    goog_data = test_stock_universe.get("GOOG", Granularity.D1).df.copy()
    broker = BacktestBroker(test_stock_universe, 100000, 0, 1, False, False, False)

    price_timestamp = (
        goog_data[:price_index].low.idxmin() if buy else goog_data[:price_index].high.idxmax()
    )
    price_idx = goog_data.index.get_loc(price_timestamp)
    price = goog_data.low.iloc[price_idx] if buy else goog_data.high.iloc[price_idx]
    limit = price + 0.01 if buy else price - 0.01  # Set to 1 cent past price
    size = 100 if buy else -100
    broker.order(Order("GOOG", size, limit=limit))

    for i in range(price_idx):
        test_stock_universe.next()
        assert len(broker.orders) == 1
        assert len(broker.trades) == 0
        assert broker.orders[0].limit == limit
        broker.next()

    # Perform one more iteration
    test_stock_universe.next()
    broker.next()

    # Should have executed on the next iteration
    assert len(broker.orders) == 0
    assert len(broker.trades) == 1
    trade = broker.trades[0]
    assert trade.entry_price == limit


@pytest.mark.parametrize("index", [1, 10, 50, 75, 100])
@pytest.mark.parametrize("buy", [True, False])
def test_stop_loss_order(index, buy, test_stock_universe: MarketData):
    goog_data = test_stock_universe.get("GOOG", Granularity.D1).df.copy()
    broker = BacktestBroker(test_stock_universe, 100000, 0, 1, False, False, False)

    stop_timestmap = goog_data[index:].low.idxmin() if buy else goog_data[index:].high.idxmax()
    stop_idx = goog_data.index.get_loc(stop_timestmap)
    stop_price = (
        goog_data.low.iloc[stop_idx] + 0.01 if buy else goog_data.high.iloc[stop_idx] - 0.01
    )
    size = 100 if buy else -100
    entry_price = goog_data.open.iloc[index]

    for i in range(index):
        test_stock_universe.next()

    # Place market order
    assert len(broker.orders) == 0
    assert len(broker.trades) == 0
    broker.order(Order("GOOG", size, stop_loss_on_fill=stop_price))
    test_stock_universe.next()
    broker.next()

    assert len(broker.orders) == (1 if stop_idx > index else 0)
    assert len(broker.trades) == (1 if stop_idx > index else 0)

    for i in range(index, stop_idx):
        assert len(broker.orders) == 1
        assert broker.orders[0].stop == stop_price
        assert len(broker.trades) == 1
        test_stock_universe.next()
        broker.next()

    # Should have executed on the last iteration
    assert len(broker.orders) == 0
    assert len(broker.trades) == 0
    assert len(broker.closed_trades) == 1
    trade = broker.closed_trades[0]
    assert trade.entry_price == entry_price
    assert trade.exit_price == stop_price


@pytest.mark.parametrize("index", [1, 10, 50, 75, 100])
@pytest.mark.parametrize("buy", [True, False])
def test_take_profit_order(index, buy, test_stock_universe: MarketData):
    goog_data = test_stock_universe.get("GOOG", Granularity.D1).df.copy()
    broker = BacktestBroker(test_stock_universe, 100000, 0, 1, False, False, False)

    limit_timestmap = goog_data[index:].high.idxmax() if buy else goog_data[index:].low.idxmin()
    limit_idx = goog_data.index.get_loc(limit_timestmap)
    limit_price = (
        goog_data.high.iloc[limit_idx] - 0.01 if buy else goog_data.low.iloc[limit_idx] + 0.01
    )
    size = 100 if buy else -100
    entry_price = goog_data.open.iloc[index]

    for i in range(index):
        test_stock_universe.next()

    # Place market order
    assert len(broker.orders) == 0
    assert len(broker.trades) == 0
    broker.order(Order("GOOG", size, take_profit_on_fill=limit_price))
    test_stock_universe.next()
    broker.next()

    assert len(broker.orders) == (1 if limit_idx > index else 0)
    assert len(broker.trades) == (1 if limit_idx > index else 0)

    for i in range(index, limit_idx):
        if len(broker.orders) == 0:
            pass
        assert len(broker.orders) == 1
        assert broker.orders[0].limit == limit_price
        assert len(broker.trades) == 1
        test_stock_universe.next()
        if i == 2137:
            pass
        broker.next()

    # Should have executed on the last iteration
    assert len(broker.orders) == 0
    assert len(broker.trades) == 0
    assert len(broker.closed_trades) == 1
    trade = broker.closed_trades[0]
    assert trade.entry_price == entry_price
    assert trade.exit_price == limit_price


def test_negative_equity(test_stock_universe: MarketData):
    broker = BacktestBroker(test_stock_universe, 200, 0, 1, False, False, False)

    broker.order(Order("GOOG", -1, stop_loss_on_fill=350))

    test_stock_universe.next()
    broker.next()

    assert len(broker.orders) == 1
    assert len(broker.trades) == 1

    for _ in range(1, 215):
        test_stock_universe.next()
        broker.next()

    test_stock_universe.next()
    with pytest.raises(OutOfMoneyError):
        broker.next()

    assert len(broker.closed_trades) == 1
    assert broker.equity == 0
    assert broker._cash == 0


def test_change_position(test_stock_universe: MarketData):
    broker = BacktestBroker(test_stock_universe, 10000, 0, 1, False, False, False)
    goog_position = broker.get_position("GOOG")

    broker.order(Order("GOOG", 100))
    test_stock_universe.next()
    broker.next()

    assert len(broker.orders) == 0
    assert len(broker.trades) == 1

    assert goog_position.is_long is True
    assert goog_position.size == 100
    assert len(goog_position.trades) == 1

    broker.order(Order("GOOG", -200))
    test_stock_universe.next()
    broker.next()

    assert goog_position.is_long is False
    assert goog_position.size == -100
    assert len(goog_position.trades) == 1


def test_close_and_open_oppposite_position(test_stock_universe: MarketData):
    broker = BacktestBroker(test_stock_universe, 10000, 0, 1, False, False, False)
    goog_position = broker.get_position("GOOG")

    broker.order(Order("GOOG", 100))
    test_stock_universe.next()
    broker.next()

    assert len(broker.orders) == 0
    assert len(broker.trades) == 1

    assert goog_position.is_long is True
    assert goog_position.size == 100
    assert len(goog_position.trades) == 1

    broker.close_position("GOOG")
    broker.order(Order("GOOG", -100))
    test_stock_universe.next()
    broker.next()

    assert goog_position.is_long is False
    assert goog_position.size == -100
    assert len(goog_position.trades) == 1


def test_close_and_open_oppposite_position_with_sl_tp(test_stock_universe: MarketData):
    broker = BacktestBroker(test_stock_universe, 10000, 0, 1, False, False, False)
    goog_position = broker.get_position("GOOG")

    broker.order(Order("GOOG", 100, stop_loss_on_fill=80, take_profit_on_fill=140))
    test_stock_universe.next()
    broker.next()

    assert len(broker.orders) == 2
    assert len(broker.trades) == 1

    assert goog_position.is_long is True
    assert goog_position.size == 100
    assert len(goog_position.trades) == 1

    broker.close_position("GOOG")
    broker.order(Order("GOOG", -100))
    test_stock_universe.next()
    broker.next()

    assert goog_position.is_long is False
    assert goog_position.size == -100
    assert len(goog_position.trades) == 1


def test_reduce_position(test_stock_universe: MarketData):
    broker = BacktestBroker(test_stock_universe, 10000, 0, 1, False, False, False)
    goog_position = broker.get_position("GOOG")

    broker.order(Order("GOOG", 100))
    test_stock_universe.next()
    broker.next()

    assert len(broker.orders) == 0
    assert len(broker.trades) == 1

    assert goog_position.is_long is True
    assert goog_position.size == 100
    assert len(goog_position.trades) == 1

    broker.order(Order("GOOG", -50))
    test_stock_universe.next()
    broker.next()

    assert goog_position.is_long is True
    assert goog_position.size == 50


def test_close_position(test_stock_universe: MarketData):
    broker = BacktestBroker(test_stock_universe, 10000, 0, 1, False, False, False)
    goog_position = broker.get_position("GOOG")

    broker.order(Order("GOOG", 100))
    test_stock_universe.next()
    broker.next()

    assert len(broker.orders) == 0
    assert len(broker.trades) == 1

    assert goog_position.is_long is True
    assert goog_position.size == 100
    assert len(goog_position.trades) == 1

    broker.order(Order("GOOG", -100))
    test_stock_universe.next()
    broker.next()

    assert goog_position.is_long is False
    assert goog_position.is_short is False
    assert goog_position.size == 0


def test_exclusive_orders(test_stock_universe: MarketData):
    broker = BacktestBroker(test_stock_universe, 10000, 0, 1, False, False, True)
    broker.order(Order("GOOG", 10))
    test_stock_universe.next()
    broker.next()

    assert len(broker.orders) == 0
    assert len(broker.trades) == 1

    broker.order(Order("GOOG", 20))

    # 1 to close existing position and then the new order
    assert len(broker.orders) == 2
    assert len(broker.trades) == 1
    assert len(broker.closed_trades) == 0

    test_stock_universe.next()
    broker.next()

    assert len(broker.orders) == 0
    assert len(broker.trades) == 1
    assert len(broker.closed_trades) == 1
