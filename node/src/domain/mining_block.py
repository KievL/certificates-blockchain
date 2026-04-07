from datetime import datetime
from pydantic import BaseModel, Field
from src.domain.transaction import Transaction


class MiningBlock(BaseModel):
    index: int
    timestamp: datetime = Field(default_factory=datetime.now)
    transactions: list[Transaction] = []
    previous_hash: str
    node_id: str
    nonce: int | None = None
    hash: str = ""

    def has_same_content(self, other: "MiningBlock") -> bool:
        """
        Two mining blocks are considered equal if they have the same
        transactions and the same previous_hash.
        """
        if self.previous_hash != other.previous_hash:
            return False

        self_tx_ids = sorted(tx.id for tx in self.transactions)
        other_tx_ids = sorted(tx.id for tx in other.transactions)
        return self_tx_ids == other_tx_ids
