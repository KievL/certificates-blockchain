from datetime import datetime
from pydantic import BaseModel
from src.domain import Transaction


class Block(BaseModel):
    timestamp: datetime
    transactions: list[Transaction]
    previous_hash: str
    hash: str
