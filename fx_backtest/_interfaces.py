from abc import abstractmethod, ABCMeta
from typing import List, Optional
from fx_backtest._models import Trade, Order

class IBroker(metaclass=ABCMeta):
    
    @property
    @abstractmethod
    def trades(self) -> List[Trade]:
        raise NotImplementedError
    
    @property
    @abstractmethod
    def orders(self) -> List[Order]:
        raise NotImplementedError

    @abstractmethod
    def new_order(
        self,
        size: float,
        limit: Optional[float] = None,
        stop: Optional[float] = None,
        sl: Optional[float] = None,
        tp: Optional[float] = None,
        tag: object = None,
        *,
        trade: Optional[Trade] = None,
    ):
        raise NotImplementedError()

    