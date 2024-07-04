from abc import abstractmethod
from fx_backtest._util import _Data
class IBroker:

    @property
    @abstractmethod
    def data(self) -> _Data:
        raise NotImplementedError()
    
    @property
    @abstractmethod
    def last_price(self) -> float:
        raise NotImplementedError()