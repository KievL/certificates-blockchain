import asyncio
import hashlib
import json
import logging

from src.domain.mining_block import MiningBlock
from src.domain.block import Block
from src.ports.events.publishers.base_publisher import IBasePublisher

logger = logging.getLogger(__name__)

_YIELD_INTERVAL = 1_000


class MiningService:
    """
    Core mining logic.

    - Listens for mining jobs (MiningBlock) and starts proof-of-work.
    - Listens for found blocks to update the last known hash and cancel
      stale mining when another miner wins.
    - Uses asyncio.Event for cooperative cancellation.
    """

    def __init__(
        self,
        publisher: IBasePublisher,
        found_blocks_topic: str,
        difficulty: int,
        miner_id: str,
    ):
        self.publisher = publisher
        self.found_blocks_topic = found_blocks_topic
        self.difficulty = difficulty
        self.miner_id = miner_id

        self._cancel_event = asyncio.Event()
        self._current_task: asyncio.Task | None = None
        self._current_mining_block: MiningBlock | None = None

    async def on_mining_job_received(self, data: dict) -> None:
        """Called when a new MiningBlock arrives from the mining_jobs topic."""
        incoming = MiningBlock(**data)
        logger.info(
            f"Received mining job: index={incoming.index}, "
            f"txs={len(incoming.transactions)}, "
            f"previous_hash={incoming.previous_hash[:8]}..."
        )

        self._cancel_current_mining()

        self._current_mining_block = incoming
        self._cancel_event.clear()
        self._current_task = asyncio.create_task(self._mine(incoming))

    async def on_block_found(self, data: dict) -> None:
        """Called when a mined Block arrives from the found_blocks topic."""
        block = Block(**data)
        logger.info(
            f"Block found by network: index={block.index}, "
            f"hash={block.hash[:8]}..., nonce={block.nonce}"
        )

        if self._current_mining_block is not None:
            if self._current_mining_block.index == block.index:
                logger.info(
                    "Another miner found this block first — cancelling our mining"
                )
                self._cancel_current_mining()

    async def _mine(self, block: MiningBlock) -> None:
        """Proof-of-work: iterate nonces until a valid hash is found."""
        target_prefix = "0" * self.difficulty
        nonce = 0

        logger.info(
            f"Starting mining: index={block.index}, difficulty={self.difficulty}"
        )

        try:
            while True:
                if self._cancel_event.is_set():
                    logger.info(f"Mining cancelled for block index={block.index}")
                    return

                hash_hex = self._compute_hash(block, nonce)

                if hash_hex.startswith(target_prefix):
                    logger.info(
                        f"Block mined! index={block.index}, "
                        f"nonce={nonce}, hash={hash_hex[:16]}..."
                    )

                    found_block = Block(
                        index=block.index,
                        timestamp=block.timestamp,
                        transactions=block.transactions,
                        previous_hash=block.previous_hash,
                        nonce=nonce,
                        hash=hash_hex,
                    )

                    await self.publisher.publish(found_block, self.found_blocks_topic)
                    self._current_mining_block = None
                    return

                nonce += 1

                # Pulo do gato
                # Yield to event loop periodically so consumers can process
                if nonce % _YIELD_INTERVAL == 0:
                    await asyncio.sleep(0)

        except asyncio.CancelledError:
            logger.info(f"Mining task cancelled for block index={block.index}")
        except Exception as e:
            logger.error(f"Error during mining: {e}", exc_info=True)

    def _cancel_current_mining(self) -> None:
        """Signal the current mining loop to stop."""
        self._cancel_event.set()
        if self._current_task and not self._current_task.done():
            self._current_task.cancel()
            logger.info("Current mining task cancelled")
        self._current_task = None
        self._current_mining_block = None

    @staticmethod
    def _compute_hash(block: MiningBlock, nonce: int) -> str:
        """Compute SHA-256 hash for a block with a given nonce."""
        data = json.dumps(
            {
                "index": block.index,
                "timestamp": str(block.timestamp),
                "transactions": [tx.model_dump() for tx in block.transactions],
                "previous_hash": block.previous_hash,
                "nonce": nonce,
            },
            sort_keys=True,
            default=str,
        )
        return hashlib.sha256(data.encode()).hexdigest()
