import binascii
try:
    from cryptography.hazmat.primitives.asymmetric import ed25519
except ImportError:
    print("Error: cryptography library not installed. Run 'pip install cryptography'")
    exit(1)

def generate_keys():
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    private_bytes = private_key.private_bytes_raw()
    public_bytes = public_key.public_bytes_raw()

    print(f"PRIVATE_KEY={binascii.hexlify(private_bytes).decode()}")
    print(f"PUBLIC_KEY={binascii.hexlify(public_bytes).decode()}")

if __name__ == "__main__":
    generate_keys()
