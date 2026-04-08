import logging
from src.domain import Block
from src.ports.repositories import IBlockRepository, ITransactionRepository, IMiningBlockRepository
from src.ports.node_client import INodeClient
from src.use_cases.receive_block import ReceiveBlock
from src.adapters.events.consumers.base_kafka_consumer import BaseKafkaConsumer

logger = logging.getLogger(__name__)


class BlockConsumer(BaseKafkaConsumer):
    def __init__(
        self,
        block_repository: IBlockRepository,
        transaction_repository: ITransactionRepository,
        mining_block_repository: IMiningBlockRepository,
        node_client: INodeClient,
        peer_urls: list[str],
        difficulty: int,
        public_key: str,
        bootstrap_servers: str,
        group_id: str,
        topic: str,
    ):
        self.use_case = ReceiveBlock(
            block_repository=block_repository,
            transaction_repository=transaction_repository,
            mining_block_repository=mining_block_repository,
            node_client=node_client,
            peer_urls=peer_urls,
            difficulty=difficulty,
            public_key=public_key,
        )
        super().__init__(bootstrap_servers, group_id, topic)

    async def process_message(self, data: dict) -> None:
        logger.info(f"Block message received from Kafka: index={data.get('index')}")
        block = Block(**data)
        await self.use_case.execute(block)
