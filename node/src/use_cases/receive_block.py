import logging
import random
from src.domain import Block
from src.ports.repositories.block_repository import IBlockRepository
from src.ports.repositories.transaction_repository import ITransactionRepository
from src.ports.repositories.mining_block_repository import IMiningBlockRepository
from src.ports.node_client import INodeClient

logger = logging.getLogger(__name__)


class ReceiveBlock:
    """
    Handles incoming blocks from the found_blocks topic.

    Responsibilities:
      1. Validate the block (hash, previous_hash, timestamp, nonce, mempool txs)
      2. Add valid blocks to the chain and remove their txs from the mempool
      3. Handle forks (keep longest chain, resolve ties)
      4. Run consensus after fork handling
    """

    def __init__(
        self,
        block_repository: IBlockRepository,
        transaction_repository: ITransactionRepository,
        mining_block_repository: IMiningBlockRepository,
        node_client: INodeClient,
        peer_urls: list[str],
        difficulty: int,
        public_key: str,
    ):
        self.block_repository = block_repository
        self.transaction_repository = transaction_repository
        self.mining_block_repository = mining_block_repository
        self.node_client = node_client
        self.peer_urls = peer_urls
        self.difficulty = difficulty
        self.public_key = public_key

    async def execute(self, block: Block) -> None:
        logger.info(f"Received block index={block.index}, hash={block.hash[:12]}...")

        # --- Basic validations ---
        if not self._validate_hash(block):
            logger.warning(f"Block {block.index} rejected: invalid hash")
            return

        if not self._validate_proof_of_work(block):
            logger.warning(
                f"Block {block.index} rejected: hash does not meet difficulty"
            )
            return

        if not self._validate_transactions_in_mempool(block):
            logger.warning(f"Block {block.index} rejected: transactions not in mempool")
            return

        if not self._validate_transaction_signatures(block):
            logger.warning(
                f"Block {block.index} rejected: invalid transaction signatures"
            )
            return

        last_block = self.block_repository.get_last_block()

        # --- Check previous_hash linkage ---
        expected_prev_hash = last_block.hash if last_block else "0"

        if block.previous_hash == expected_prev_hash:
            # Normal case: block extends the current chain
            if not self._validate_timestamp(block, last_block):
                logger.warning(f"Block {block.index} rejected: invalid timestamp")
                return

            self._accept_block(block)
            logger.info(f"Block {block.index} accepted into chain")
        else:
            # Fork detected
            logger.warning(
                f"Fork detected! Block previous_hash={block.previous_hash[:12]}... "
                f"does not match expected={expected_prev_hash[:12]}..."
            )
            await self._handle_fork(block)

    # ------------------------------------------------------------------ #
    #  Validation helpers                                                  #
    # ------------------------------------------------------------------ #

    def _validate_hash(self, block: Block) -> bool:
        """Recompute the hash and verify it matches the block's hash field."""
        computed = block.compute_hash()
        if computed != block.hash:
            logger.warning(
                f"Hash mismatch: computed={computed[:12]}... "
                f"vs block.hash={block.hash[:12]}..."
            )
            return False
        return True

    def _validate_proof_of_work(self, block: Block) -> bool:
        """Check that the hash meets the difficulty requirement."""
        return block.is_hash_valid(self.difficulty)

    def _validate_timestamp(self, block: Block, previous_block: Block | None) -> bool:
        """Ensure the block's timestamp is strictly after the previous block's."""
        if previous_block is None:
            return True
        return block.timestamp > previous_block.timestamp

    def _validate_transactions_in_mempool(self, block: Block) -> bool:
        """Verify that every transaction in the block exists in the mempool."""
        mempool_ids = {tx.id for tx in self.transaction_repository.list()}
        for tx in block.transactions:
            if tx.id not in mempool_ids:
                logger.debug(f"Transaction {tx.id} not found in mempool")
                return False
        return True

    def _validate_transaction_signatures(self, block: Block) -> bool:
        """Verify the signature of every transaction in the block."""
        invalid_detected = False
        for tx in block.transactions:
            if not tx.is_signature_valid(self.public_key):
                logger.warning(
                    f"Transaction {tx.id} has invalid signature! Purging from mempool."
                )
                try:
                    self.transaction_repository.remove(tx.id)
                except ValueError:
                    pass
                invalid_detected = True

        return not invalid_detected

    # ------------------------------------------------------------------ #
    #  Block acceptance                                                    #
    # ------------------------------------------------------------------ #

    def _accept_block(self, block: Block) -> None:
        """Add block to chain, remove its txs from mempool, clear mining blocks."""
        try:
            self.block_repository.add(block)
        except ValueError:
            logger.debug("Block already in chain, skipping")
            return

        for tx in block.transactions:
            try:
                self.transaction_repository.remove(tx.id)
            except ValueError:
                pass

        self.mining_block_repository.clear()

    # ------------------------------------------------------------------ #
    #  Fork handling                                                       #
    # ------------------------------------------------------------------ #

    async def _handle_fork(self, incoming_block: Block) -> None:
        """
        Handle a fork by comparing chain lengths.

        - If the incoming fork is longer → switch to it
        - If equal → keep current chain, return exclusive txs to mempool
        - After any fork, run consensus
        """
        current_chain = self.block_repository.get_chain()

        # Build the fork chain: find where the incoming block branches from
        fork_chain = self._build_fork_chain(incoming_block, current_chain)

        if fork_chain is None:
            logger.warning("Could not reconstruct fork chain — discarding block")
            await self._run_consensus()
            return

        # Find the fork point
        fork_point = self._find_fork_point(fork_chain, current_chain)

        current_branch_len = len(current_chain) - fork_point
        fork_branch_len = len(fork_chain) - fork_point

        logger.info(
            f"Fork analysis: current_branch={current_branch_len} blocks, "
            f"incoming_branch={fork_branch_len} blocks, fork_point={fork_point}"
        )

        if fork_branch_len > current_branch_len:
            # Incoming fork is longer — switch to it
            logger.info("Incoming fork is longer — switching chains")
            discarded_blocks = current_chain[fork_point:]
            self._return_exclusive_txs_to_mempool(
                discarded_blocks, fork_chain[fork_point:]
            )
            self.block_repository.replace_chain(fork_chain)
        elif fork_branch_len == current_branch_len:
            # Tie — keep current chain, return exclusive txs from incoming
            logger.info("Fork tie — keeping current chain")
            self._return_exclusive_txs_to_mempool([incoming_block], current_chain)
        else:
            # Current chain is longer — discard incoming block
            logger.info("Current chain is longer — discarding incoming block")

        # Always run consensus after fork handling
        await self._run_consensus()

    def _build_fork_chain(
        self, incoming_block: Block, current_chain: list[Block]
    ) -> list[Block] | None:
        """
        Reconstruct the fork chain by prepending blocks from the current chain
        that share the same ancestry, then appending the incoming block.
        """
        # Find the common ancestor in the current chain
        common_prefix: list[Block] = []
        for block in current_chain:
            if block.hash == incoming_block.previous_hash:
                common_prefix = current_chain[: current_chain.index(block) + 1]
                break

        if not common_prefix and incoming_block.previous_hash != "0":
            # The incoming block's parent is not in our chain at all
            return None

        return common_prefix + [incoming_block]

    def _find_fork_point(self, chain_a: list[Block], chain_b: list[Block]) -> int:
        """Find the index where two chains diverge."""
        min_len = min(len(chain_a), len(chain_b))
        for i in range(min_len):
            if chain_a[i].hash != chain_b[i].hash:
                return i
        return min_len

    def _return_exclusive_txs_to_mempool(
        self,
        discarded_blocks: list[Block],
        kept_blocks: list[Block],
    ) -> None:
        """
        Return transactions that are in the discarded branch but NOT in the
        kept branch back to the mempool.
        """
        kept_tx_ids: set[str] = set()
        for block in kept_blocks:
            for tx in block.transactions:
                kept_tx_ids.add(tx.id)

        for block in discarded_blocks:
            for tx in block.transactions:
                if tx.id not in kept_tx_ids:
                    try:
                        self.transaction_repository.add(tx)
                        logger.info(
                            f"Returned tx {tx.id} to mempool from discarded branch"
                        )
                    except ValueError:
                        pass  # Already in mempool

    # ------------------------------------------------------------------ #
    #  Consensus                                                           #
    # ------------------------------------------------------------------ #

    async def _run_consensus(self) -> None:
        """
        Consensus protocol: fetch chains from 2 random peer nodes.

        - If both peers return chains that are equal to each other AND longer
          than our chain → adopt theirs.
        - Otherwise → keep our chain.
        """
        if len(self.peer_urls) < 2:
            logger.warning("Not enough peers for consensus")
            return

        selected_peers = random.sample(self.peer_urls, 2)
        logger.info(f"Running consensus with peers: {selected_peers}")

        chain_a = await self.node_client.get_chain(selected_peers[0])
        chain_b = await self.node_client.get_chain(selected_peers[1])

        if not chain_a or not chain_b:
            logger.warning("Could not fetch chains from peers — keeping current")
            return

        my_chain = self.block_repository.get_chain()

        # Check if both peer chains are equal
        if len(chain_a) != len(chain_b):
            logger.info(
                f"Peer chains differ in length ({len(chain_a)} vs {len(chain_b)}) "
                "— keeping current chain"
            )
            return

        chains_equal = all(a.hash == b.hash for a, b in zip(chain_a, chain_b))

        if not chains_equal:
            logger.info("Peer chains are not equal — keeping current chain")
            return

        if len(chain_a) > len(my_chain):
            logger.info(
                f"Peers have a longer chain ({len(chain_a)} > {len(my_chain)}) "
                "and agree — adopting their chain"
            )
            # Return exclusive txs from our discarded blocks to the mempool
            fork_point = self._find_fork_point(my_chain, chain_a)
            self._return_exclusive_txs_to_mempool(
                my_chain[fork_point:], chain_a[fork_point:]
            )
            self.block_repository.replace_chain(chain_a)
            self.mining_block_repository.clear()
        else:
            logger.info(
                f"Our chain is same length or longer "
                f"({len(my_chain)} >= {len(chain_a)}) — keeping current"
            )
