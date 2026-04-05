from abc import ABC, abstractmethod
from src.domain import Transaction


class ITransactionEventsPublisher(ABC):
    @abstractmethod
    async def publish(self, transaction: Transaction) -> None:
        pass
