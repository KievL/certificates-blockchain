import hashlib
import json
from datetime import datetime

from pydantic import BaseModel

from src.domain import Transaction


class Block(BaseModel):
    index: int
    timestamp: datetime
    transactions: list[Transaction]
    previous_hash: str
    nonce: int = 0
    hash: str = ""
    force_accept: bool = False

    def compute_hash(self) -> str:
        """Recompute the SHA-256 hash for this block (same logic as the miner)."""
        data = json.dumps(
            {
                "index": self.index,
                "timestamp": str(self.timestamp),
                "transactions": [tx.model_dump() for tx in self.transactions],
                "previous_hash": self.previous_hash,
                "nonce": self.nonce,
            },
            sort_keys=True,
            default=str,
        )
        return hashlib.sha256(data.encode()).hexdigest()

    def is_hash_valid(self, difficulty: int) -> bool:
        """Check whether the hash starts with the required number of leading zeros."""
        return self.hash.startswith("0" * difficulty)
