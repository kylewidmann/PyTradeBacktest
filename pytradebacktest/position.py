import numpy as np
from pytrade.instruments import Instrument
from pytrade.interfaces.position import IPosition
from pytrade.models import Trade


class Position(IPosition):
    """
    Currently held asset position, available as
    `backtesting.backtesting.Strategy.position` within
    `backtesting.backtesting.Strategy.next`.
    Can be used in boolean contexts, e.g.

        if self.position:
            ...  # we have a position, either long or short
    """

    def __init__(self, instrument: Instrument, trades: list[Trade]):
        self.__instrument = instrument
        self.__trades = trades

    def __bool__(self):
        return self.size != 0

    @property
    def trades(self):
        return [trade for trade in self.__trades if trade.instrument == self.__instrument]

    @property
    def size(self) -> float:
        """Position size in units of asset. Negative if position is short."""
        return sum(trade.size for trade in self.trades)

    @property
    def pl(self) -> float:
        """Profit (positive) or loss (negative) of the current position in cash units."""
        return sum(trade.pl for trade in self.trades)

    @property
    def pl_pct(self) -> float:
        """Profit (positive) or loss (negative) of the current position in percent."""
        weights = np.abs([trade.size for trade in self.trades])
        weights = weights / weights.sum()
        pl_pcts = np.array([trade.pl_pct for trade in self.trades])
        return (pl_pcts * weights).sum()

    @property
    def is_long(self) -> bool:
        """True if the position is long (position size is positive)."""
        return self.size > 0

    @property
    def is_short(self) -> bool:
        """True if the position is short (position size is negative)."""
        return self.size < 0

    def __repr__(self):
        return f"<Position[{self.__instrument}]: {self.size} ({len(self.trades)} trades)>"
