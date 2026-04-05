from src.domain import Transaction, Block
from src.ports.repositories import ITransactionRepository, IBlockRepository
from src.use_cases.receive_transaction import ReceiveTransaction
from src.use_cases.receive_block import ReceiveBlock
from src.adapters.events.kafka_consumer import BaseKafkaConsumer


class TransactionKafkaConsumer(BaseKafkaConsumer):
    def __init__(
        self,
        bootstrap_servers: str,
        topic: str,
        repository: ITransactionRepository,
        group_id: str,
    ):
        super().__init__(bootstrap_servers, topic, group_id)
        self.use_case = ReceiveTransaction(repository=repository)

    async def process_message(self, data: dict):
        transaction = Transaction(**data)
        self.use_case.execute(transaction)


class BlockKafkaConsumer(BaseKafkaConsumer):
    def __init__(
        self,
        bootstrap_servers: str,
        topic: str,
        block_repository: IBlockRepository,
        transaction_repository: ITransactionRepository,
        group_id: str,
    ):
        super().__init__(bootstrap_servers, topic, group_id)
        self.use_case = ReceiveBlock(
            block_repository=block_repository,
            transaction_repository=transaction_repository,
        )

    async def process_message(self, data: dict):
        block = Block(**data)
        self.use_case.execute(block)
