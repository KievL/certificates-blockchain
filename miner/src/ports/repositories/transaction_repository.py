from abc import ABC, abstractmethod
from src.domain import Transaction


class ITransactionRepository(ABC):
    _mempool: list[Transaction]

    @abstractmethod
    def add(self, transaction: Transaction) -> None:
        pass

    @abstractmethod
    def get(self, id: str) -> Transaction:
        pass

    @abstractmethod
    def list(self) -> list[Transaction]:
        pass

    @abstractmethod
    def remove(self, id: str) -> None:
        pass

    @abstractmethod
    def get_size(self) -> int:
        pass

    @abstractmethod
    def clear(self) -> None:
        pass
