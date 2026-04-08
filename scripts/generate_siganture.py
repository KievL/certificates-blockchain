import json
import binascii
import uuid
from datetime import datetime
from cryptography.hazmat.primitives.asymmetric import ed25519

PRIVATE_KEY_HEX = "e0cf425e0b20bec6bec3ff1ee9e1dd39c4ba08b94afd21866cf371b90b77efed"  # Gerada pelo generate_keys.py


def sign_and_print():
    payload = {
        "person_name": "Kiev Lima",
        "person_email": "kiev@example.com",
        "course": "Sistemas Distribuídos",
        "certification_date": "2026-04-08",
        "institution": "UFRN",
    }

    tx_id = str(uuid.uuid4())
    timestamp = datetime.now()
    timestamp_str = str(timestamp)

    signable_dict = {
        "id": tx_id,
        "timestamp": timestamp_str,
        "payload": payload,
    }
    data_to_sign = json.dumps(signable_dict, sort_keys=True).encode()

    private_key_bytes = bytes.fromhex(PRIVATE_KEY_HEX)
    private_key = ed25519.Ed25519PrivateKey.from_private_bytes(private_key_bytes)
    signature = private_key.sign(data_to_sign)
    signature_hex = binascii.hexlify(signature).decode()

    signable_dict.update({"signature": signature_hex})

    print(json.dumps(signable_dict, indent=2))


if __name__ == "__main__":
    sign_and_print()
