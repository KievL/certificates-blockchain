import json
from aiokafka import AIOKafkaConsumer
from src.ports.events.consumers.base_consumer import IBaseConsumer

import asyncio
import logging
from aiokafka.errors import KafkaConnectionError
from abc import abstractmethod


class BaseKafkaConsumer(IBaseConsumer):
    def __init__(self, bootstrap_servers: str, group_id: str, topic: str):
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.topic = topic
        self.consumer = None
        self.is_running = False

    async def start(self):
        self.consumer = AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.group_id,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        )

        while True:
            try:
                await self.consumer.start()
                logging.info(f"Kafka Consumer ({self.topic}) started successfully")
                break
            except (KafkaConnectionError, Exception) as e:
                logging.error(
                    f"Failed to start Kafka Consumer ({self.topic}), retrying in 2 seconds... {e}"
                )
                await asyncio.sleep(2)

        self.is_running = True

        try:
            async for msg in self.consumer:
                if not self.is_running:
                    break
                await self.process_message(msg.value)
        except Exception as e:
            logging.error(f"Error in Kafka consumer ({self.topic}): {e}", exc_info=True)
        finally:
            await self.consumer.stop()

    async def stop(self):
        self.is_running = False
        if self.consumer:
            await self.consumer.stop()

    @abstractmethod
    async def process_message(self, data: dict) -> None: ...
