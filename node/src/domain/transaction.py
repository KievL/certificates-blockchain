from datetime import datetime
import json
from pydantic import BaseModel, Field
import uuid
from cryptography.hazmat.primitives.asymmetric import ed25519


class CertificatePayload(BaseModel):
    person_name: str
    person_email: str
    course: str
    certification_date: str
    institution: str


class Transaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    payload: CertificatePayload
    signature: str | None = None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Transaction):
            return False
        return self.id == other.id

    def get_signable_data(self) -> bytes:
        """Returns a stable byte representation of the transaction data for signing/verification."""
        data = {
            "id": self.id,
            "timestamp": str(self.timestamp),
            "payload": self.payload.model_dump(),
        }
        return json.dumps(data, sort_keys=True).encode()

    def is_signature_valid(self, public_key_hex: str) -> bool:
        """Verifies if the transaction signature is valid for the given public key."""
        if not self.signature:
            return False

        try:
            public_key_bytes = bytes.fromhex(public_key_hex)
            public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)
            
            signature_bytes = bytes.fromhex(self.signature)
            data_bytes = self.get_signable_data()
            
            public_key.verify(signature_bytes, data_bytes)
            return True
        except Exception:
            return False
