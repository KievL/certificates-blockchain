from src.domain import Transaction
from src.ports.repositories import ITransactionRepository
from src.use_cases.receive_transaction import ReceiveTransaction
from src.use_cases.mining_job_service import MiningJobService
from src.adapters.events.consumers.base_kafka_consumer import BaseKafkaConsumer


class TransactionConsumer(BaseKafkaConsumer):
    def __init__(
        self,
        transaction_repository: ITransactionRepository,
        mining_job_service: MiningJobService,
        bootstrap_servers: str,
        group_id: str,
        topic: str,
        public_key: str,
    ):
        self.use_case = ReceiveTransaction(
            repository=transaction_repository, public_key=public_key
        )
        self.mining_job_service = mining_job_service
        super().__init__(bootstrap_servers, group_id, topic)

    async def process_message(self, data: dict) -> None:
        transaction = Transaction(**data)
        self.use_case.execute(transaction)
        await self.mining_job_service.on_transaction_received()
