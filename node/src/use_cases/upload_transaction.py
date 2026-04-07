from src.domain import Transaction
from src.ports.repositories import ITransactionRepository
from src.ports.events.publishers.base_publisher import IBasePublisher
from src.use_cases.mining_job_service import MiningJobService


class UploadTransaction:
    def __init__(
        self,
        repository: ITransactionRepository,
        publisher: IBasePublisher,
        mining_job_service: MiningJobService,
    ):
        self.repository = repository
        self.publisher = publisher
        self.mining_job_service = mining_job_service

    async def execute(self, payload: Transaction, topic: str) -> Transaction:
        self.repository.add(payload)
        await self.publisher.publish(payload, topic)
        await self.mining_job_service.on_transaction_received()
        return payload
