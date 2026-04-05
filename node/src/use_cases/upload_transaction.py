from src.domain import Transaction
from src.ports.repositories import ITransactionRepository
from src.ports.events.transaction_events import ITransactionEventsPublisher


class UploadTransaction:
    def __init__(
        self, repository: ITransactionRepository, publisher: ITransactionEventsPublisher
    ):
        self.repository = repository
        self.publisher = publisher

    async def execute(self, payload: Transaction) -> Transaction:
        self.repository.add(payload)
        await self.publisher.publish(payload)
        return payload
