import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from src.entrypoints.schemas import TransactionRequest

from src.domain import Transaction, Block
from src.adapters.repositories import (
    TransactionInMemoryRepository,
    BlockInMemoryRepository,
)
from src.adapters.events.kafka_transaction_events_publisher import (
    KafkaTransactionEventsPublisher,
)
from src.use_cases.upload_transaction import UploadTransaction
from src.use_cases.list_blocks import ListBlocks
from src.use_cases.list_transactions import ListTransactions
from src.entrypoints.events import (
    TransactionKafkaConsumer,
    BlockKafkaConsumer,
)
from src.config import settings

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# a gnt pode depois usar alguma lib de dependency injection
transaction_repository = TransactionInMemoryRepository()
block_repository = BlockInMemoryRepository()

publisher = KafkaTransactionEventsPublisher(
    bootstrap_servers=settings.KAFKA_BROKER, topic=settings.TRANSACTIONS_TOPIC
)

upload_transaction_use_case = UploadTransaction(
    repository=transaction_repository, publisher=publisher
)
list_blocks_use_case = ListBlocks(repository=block_repository)
list_transactions_use_case = ListTransactions(repository=transaction_repository)

transaction_consumer = TransactionKafkaConsumer(
    bootstrap_servers=settings.KAFKA_BROKER,
    topic=settings.TRANSACTIONS_TOPIC,
    repository=transaction_repository,
    group_id=settings.NODE_ID,
)

block_consumer = BlockKafkaConsumer(
    bootstrap_servers=settings.KAFKA_BROKER,
    topic=settings.BLOCKS_TOPIC,
    block_repository=block_repository,
    transaction_repository=transaction_repository,
    group_id=settings.NODE_ID,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """
    Função que é chamada quando a aplicação é iniciada e quando é encerrada.
    """
    await publisher.start()

    tx_consumer_task = asyncio.create_task(transaction_consumer.start())
    block_consumer_task = asyncio.create_task(block_consumer.start())

    yield

    await publisher.stop()
    await transaction_consumer.stop()
    await block_consumer.stop()

    tx_consumer_task.cancel()
    block_consumer_task.cancel()

    try:
        await asyncio.gather(tx_consumer_task, block_consumer_task)
    except asyncio.CancelledError:
        pass


app = FastAPI(title=f"Blockchain Node {settings.NODE_ID}", lifespan=lifespan)


@app.post("/transactions", response_model=Transaction)
async def upload_transaction(request: TransactionRequest):
    try:
        return await upload_transaction_use_case.execute(request.to_domain())
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
