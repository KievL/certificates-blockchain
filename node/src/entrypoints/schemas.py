from datetime import datetime
from pydantic import BaseModel
from src.domain import Transaction, CertificatePayload


class TransactionRequest(BaseModel):
    id: str | None = None
    timestamp: datetime | None = None
    payload: CertificatePayload
    signature: str | None = None

    def to_domain(self) -> Transaction:
        return Transaction(
            id=self.id or Transaction.model_fields["id"].default_factory(),
            timestamp=self.timestamp or datetime.now(),
            payload=self.payload,
            signature=self.signature,
        )
