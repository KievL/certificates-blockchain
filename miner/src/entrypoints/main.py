import asyncio
import logging
import signal

from src.config import settings

from src.adapters.events.publishers.base_kafka_publisher import BaseKafkaPublisher
from src.adapters.events.consumers.mining_job_consumer import MiningJobConsumer
from src.adapters.events.consumers.found_block_consumer import FoundBlockConsumer

from src.use_cases.mining_service import MiningService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


async def main():
    logger.info(
        f"Starting Miner {settings.MINER_ID} (difficulty={settings.DIFFICULTY})"
    )

    publisher = BaseKafkaPublisher(bootstrap_servers=settings.KAFKA_BROKER)

    mining_service = MiningService(
        publisher=publisher,
        found_blocks_topic=settings.FOUND_BLOCKS_TOPIC,
        difficulty=settings.DIFFICULTY,
        miner_id=settings.MINER_ID,
    )

    mining_job_consumer = MiningJobConsumer(
        mining_service=mining_service,
        bootstrap_servers=settings.KAFKA_BROKER,
        group_id=settings.MINER_ID,
        topic=settings.MINING_JOBS_TOPIC,
    )

    found_block_consumer = FoundBlockConsumer(
        mining_service=mining_service,
        bootstrap_servers=settings.KAFKA_BROKER,
        group_id=settings.MINER_ID,
        topic=settings.FOUND_BLOCKS_TOPIC,
    )

    await publisher.start()

    mining_job_task = asyncio.create_task(mining_job_consumer.start())
    found_block_task = asyncio.create_task(found_block_consumer.start())

    logger.info(f"Miner {settings.MINER_ID} is running")

    stop_event = asyncio.Event()

    def _signal_handler():
        logger.info("Shutdown signal received")
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _signal_handler)

    await stop_event.wait()

    logger.info("Shutting down...")

    await mining_job_consumer.stop()
    await found_block_consumer.stop()
    await publisher.stop()

    mining_job_task.cancel()
    found_block_task.cancel()

    try:
        await asyncio.gather(mining_job_task, found_block_task)
    except asyncio.CancelledError:
        pass

    logger.info(f"Miner {settings.MINER_ID} stopped")


if __name__ == "__main__":
    asyncio.run(main())
