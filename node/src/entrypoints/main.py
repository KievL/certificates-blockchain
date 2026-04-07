import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException

from src.entrypoints.schemas import TransactionRequest
from src.domain import Transaction, Block
from src.config import settings

from src.adapters.repositories import (
    TransactionInMemoryRepository,
    BlockInMemoryRepository,
    MiningBlockInMemoryRepository,
)

from src.adapters.events.publishers.base_kafka_publisher import BaseKafkaPublisher

from src.adapters.jobs.asyncio_job_manager import AsyncIOJobManager

from src.adapters.events.consumers.transaction_consumer import TransactionConsumer
from src.adapters.events.consumers.block_consumer import BlockConsumer
from src.adapters.events.consumers.mining_block_consumer import MiningBlockConsumer

from src.use_cases.upload_transaction import UploadTransaction
from src.use_cases.list_blocks import ListBlocks
from src.use_cases.list_transactions import ListTransactions
from src.use_cases.mining_job_service import MiningJobService

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


transaction_repository = TransactionInMemoryRepository()
block_repository = BlockInMemoryRepository()
mining_block_repository = MiningBlockInMemoryRepository()

publisher = BaseKafkaPublisher(bootstrap_servers=settings.KAFKA_BROKER)

job_manager = AsyncIOJobManager()

mining_job_service = MiningJobService(
    transaction_repository=transaction_repository,
    mining_block_repository=mining_block_repository,
    block_repository=block_repository,
    publisher=publisher,
    job_manager=job_manager,
    mining_jobs_topic=settings.MINING_JOBS_TOPIC,
    batch_size=settings.BATCH_SIZE,
    mining_timeout_seconds=settings.MINING_TIMEOUT_SECONDS,
    jitter_max_seconds=settings.JITTER_MAX_SECONDS,
    node_id=settings.NODE_ID,
)

upload_transaction_use_case = UploadTransaction(
    repository=transaction_repository,
    publisher=publisher,
    mining_job_service=mining_job_service,
)
list_blocks_use_case = ListBlocks(repository=block_repository)
list_transactions_use_case = ListTransactions(repository=transaction_repository)

transaction_consumer = TransactionConsumer(
    transaction_repository=transaction_repository,
    mining_job_service=mining_job_service,
    bootstrap_servers=settings.KAFKA_BROKER,
    topic=settings.TRANSACTIONS_TOPIC,
    group_id=settings.NODE_ID,
)

mining_block_consumer = MiningBlockConsumer(
    mining_job_service=mining_job_service,
    bootstrap_servers=settings.KAFKA_BROKER,
    topic=settings.MINING_JOBS_TOPIC,
    group_id=settings.NODE_ID,
)

block_consumer = BlockConsumer(
    block_repository=block_repository,
    transaction_repository=transaction_repository,
    bootstrap_servers=settings.KAFKA_BROKER,
    topic=settings.FOUND_BLOCKS_TOPIC,
    group_id=settings.NODE_ID,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Start/stop publisher and consumer tasks with the application."""
    await publisher.start()

    tx_consumer_task = asyncio.create_task(transaction_consumer.start())
    mining_consumer_task = asyncio.create_task(mining_block_consumer.start())
    block_consumer_task = asyncio.create_task(block_consumer.start())

    yield

    await publisher.stop()
    await transaction_consumer.stop()
    await mining_block_consumer.stop()
    await block_consumer.stop()

    tx_consumer_task.cancel()
    mining_consumer_task.cancel()
    block_consumer_task.cancel()

    try:
        await asyncio.gather(
            tx_consumer_task, mining_consumer_task, block_consumer_task
        )
    except asyncio.CancelledError:
        pass


app = FastAPI(title=f"Blockchain Node {settings.NODE_ID}", lifespan=lifespan)


@app.post("/transactions", response_model=Transaction)
async def upload_transaction(request: TransactionRequest):
    try:
        return await upload_transaction_use_case.execute(
            request.to_domain(), settings.TRANSACTIONS_TOPIC
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/blocks", response_model=list[Block])
async def list_blocks():
    return list_blocks_use_case.execute()


@app.get("/transactions", response_model=list[Transaction])
async def list_transactions():
    return list_transactions_use_case.execute()


@app.get("/health")
async def health_check():
    return {"status": "ok", "node_id": settings.NODE_ID}
