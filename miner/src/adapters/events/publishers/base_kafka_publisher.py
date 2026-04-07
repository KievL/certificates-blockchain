from pydantic import BaseModel
import json
import logging
import asyncio
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaConnectionError
from src.ports.events.publishers.base_publisher import IBasePublisher


class BaseKafkaPublisher(IBasePublisher):
    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self.producer = None

    async def start(self):
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
        )
        while True:
            try:
                await self.producer.start()
                logging.info("Kafka Producer started successfully")
                break
            except (KafkaConnectionError, Exception) as e:
                logging.error(
                    f"Failed to start Kafka Producer, retrying in 2 seconds... {e}"
                )
                await asyncio.sleep(2)

    async def stop(self):
        if self.producer:
            await self.producer.stop()

    async def publish(self, message: BaseModel, topic: str) -> None:
        if not self.producer:
            await self.start()

        data = message.model_dump()
        await self.producer.send_and_wait(topic, data)
        logging.info(f"Published message to topic {topic}")
