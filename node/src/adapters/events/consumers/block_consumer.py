from src.domain import Block
from src.ports.repositories import IBlockRepository, ITransactionRepository
from src.use_cases.receive_block import ReceiveBlock
from src.adapters.events.consumers.base_kafka_consumer import BaseKafkaConsumer


class BlockConsumer(BaseKafkaConsumer):
    def __init__(
        self,
        block_repository: IBlockRepository,
        transaction_repository: ITransactionRepository,
        bootstrap_servers: str,
        group_id: str,
        topic: str,
    ):
        self.use_case = ReceiveBlock(
            block_repository=block_repository,
            transaction_repository=transaction_repository,
        )
        super().__init__(bootstrap_servers, group_id, topic)

    async def process_message(self, data: dict) -> None:
        block = Block(**data)
        self.use_case.execute(block)
