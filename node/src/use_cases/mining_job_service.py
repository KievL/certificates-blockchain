import asyncio
import random
import logging


from src.domain.mining_block import MiningBlock
from src.domain.transaction import Transaction
from src.ports.repositories.transaction_repository import ITransactionRepository
from src.ports.repositories.mining_block_repository import IMiningBlockRepository
from src.ports.repositories.block_repository import IBlockRepository
from src.ports.events.publishers.base_publisher import IBasePublisher
from src.ports.jobs.base_job_manager import IBaseJobManager

logger = logging.getLogger(__name__)


class MiningJobService:
    """
    Orchestrates the creation and publishing of mining blocks.

    Monitors the mempool and creates mining blocks when:
      - The number of eligible transactions reaches BATCH_SIZE
      - A timeout of MINING_TIMEOUT_SECONDS is reached (even with fewer txs)

    Before publishing, a jitter delay is applied. After jitter the service
    re-checks whether another node already published an equivalent block
    (same transactions + same previous_hash) to avoid duplicates.
    """

    def __init__(
        self,
        transaction_repository: ITransactionRepository,
        mining_block_repository: IMiningBlockRepository,
        block_repository: IBlockRepository,
        publisher: IBasePublisher,
        job_manager: IBaseJobManager,
        mining_jobs_topic: str,
        batch_size: int,
        mining_timeout_seconds: float,
        jitter_max_seconds: float,
        node_id: str,
    ):
        self.transaction_repository = transaction_repository
        self.mining_block_repository = mining_block_repository
        self.block_repository = block_repository
        self.publisher = publisher
        self.job_manager = job_manager
        self.mining_jobs_topic = mining_jobs_topic
        self.batch_size = batch_size
        self.mining_timeout_seconds = mining_timeout_seconds
        self.jitter_max_seconds = jitter_max_seconds
        self.node_id = node_id

    async def on_transaction_received(self) -> None:
        """Called after a new transaction is added to the mempool."""
        eligible = self._get_eligible_transactions()
        logger.info(
            f"Transaction received — {len(eligible)} eligible txs "
            f"(batch_size={self.batch_size})"
        )

        if len(eligible) >= self.batch_size:
            await self._create_mining_block()
            return

        if not self.job_manager.is_job_pending():
            logger.info(f"Starting timeout timer ({self.mining_timeout_seconds}s)")
            self.job_manager.schedule_job(
                delay=self.mining_timeout_seconds,
                callback=self._on_timeout,
            )

    async def on_mining_job_received(self, data: dict) -> None:
        """Called when a mining block from another node arrives via Kafka."""
        incoming = MiningBlock(**data)
        logger.info(
            f"Received mining block from node {incoming.node_id} "
            f"with {len(incoming.transactions)} txs"
        )

        try:
            self.mining_block_repository.add(incoming)
        except ValueError:
            logger.debug("Mining block already stored, skipping")
            return

        if self.job_manager.is_job_pending():
            eligible = self._get_eligible_transactions()
            if len(eligible) < self.batch_size:
                logger.info(
                    "Incoming mining block covers our eligible txs — "
                    "cancelling pending job"
                )
                self.job_manager.cancel_job()

    async def _on_timeout(self) -> None:
        """Callback fired when the timeout timer expires."""
        logger.info("Mining timeout reached — attempting to create block")
        await self._create_mining_block()

    async def _create_mining_block(self) -> None:
        """
        Build a mining block from eligible transactions, apply jitter,
        re-check for duplicates, then publish.
        """
        self.job_manager.cancel_job()

        eligible = self._get_eligible_transactions()
        if not eligible:
            logger.info("No eligible transactions — skipping block creation")
            return

        selected = eligible[: self.batch_size]

        last_block = self.block_repository.get_last_block()
        previous_hash = last_block.hash if last_block else "0"
        block_index = (last_block.index + 1) if last_block else 0

        candidate = MiningBlock(
            index=block_index,
            transactions=selected,
            previous_hash=previous_hash,
            node_id=self.node_id,
        )

        jitter = random.uniform(0, self.jitter_max_seconds)
        logger.info(f"Applying jitter of {jitter:.2f}s before publishing")
        await asyncio.sleep(jitter)

        if self._is_duplicate(candidate):
            logger.info(
                "Another node already published an equivalent mining block — skipping"
            )
            return

        await self.publisher.publish(candidate, self.mining_jobs_topic)
        try:
            self.mining_block_repository.add(candidate)
        except ValueError:
            pass

        logger.info(
            f"Mining block published to {self.mining_jobs_topic} "
            f"with {len(selected)} txs (index={block_index})"
        )

        remaining = self._get_eligible_transactions()
        if remaining:
            logger.info(
                f"{len(remaining)} eligible txs remaining — restarting timeout timer"
            )
            self.job_manager.schedule_job(
                delay=self.mining_timeout_seconds,
                callback=self._on_timeout,
            )

    def _get_eligible_transactions(self) -> list[Transaction]:
        """
        Returns mempool transactions that are NOT already included
        in any known mining block.
        """
        all_txs = self.transaction_repository.list()
        used_tx_ids: set[str] = set()

        for mb in self.mining_block_repository.list():
            for tx in mb.transactions:
                used_tx_ids.add(tx.id)

        return [tx for tx in all_txs if tx.id not in used_tx_ids]

    def _is_duplicate(self, candidate: MiningBlock) -> bool:
        """
        Check whether an equivalent mining block (same transactions
        + same previous_hash) already exists in the repository.
        """
        for existing in self.mining_block_repository.list():
            if candidate.has_same_content(existing):
                return True
        return False
