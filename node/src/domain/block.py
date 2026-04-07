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
