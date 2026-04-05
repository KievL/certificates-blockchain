from pydantic import BaseModel
from src.domain import Transaction


class TransactionRequest(BaseModel):
    payload: dict

    def to_domain(self) -> Transaction:
        return Transaction(payload=self.payload)
