from datetime import datetime
from pydantic import BaseModel, Field
import uuid


class Transaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    payload: dict

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Transaction):
            return False
        return self.id == other.id
