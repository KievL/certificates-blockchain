from __future__ import annotations
from typing import TYPE_CHECKING

from src.adapters.events.consumers.base_kafka_consumer import BaseKafkaConsumer

if TYPE_CHECKING:
    from src.use_cases.mining_service import MiningService


class MiningJobConsumer(BaseKafkaConsumer):
    def __init__(
        self,
        mining_service: MiningService,
        bootstrap_servers: str,
        group_id: str,
        topic: str,
    ):
        self.mining_service = mining_service
        super().__init__(bootstrap_servers, group_id, topic)

    async def process_message(self, data: dict) -> None:
        await self.mining_service.on_mining_job_received(data)
