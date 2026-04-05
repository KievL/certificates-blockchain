import json
from aiokafka import AIOKafkaProducer
from src.domain import Transaction
from src.ports.events.transaction_events import ITransactionEventsPublisher


import asyncio
import logging
from aiokafka.errors import KafkaConnectionError


class KafkaTransactionEventsPublisher(ITransactionEventsPublisher):
    def __init__(self, bootstrap_servers: str, topic: str):
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
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

    async def publish(self, transaction: Transaction) -> None:
        if not self.producer:
            raise RuntimeError("Producer not started")

        await self.producer.send_and_wait(self.topic, transaction.model_dump())
