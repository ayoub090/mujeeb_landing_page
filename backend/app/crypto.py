import base64
import hashlib
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config import get_settings


def _key() -> bytes:
    raw = get_settings().data_encryption_key
    if raw:
        try:
            padded = raw + "=" * (-len(raw) % 4)
            key = base64.urlsafe_b64decode(padded)
        except Exception as exc:
            raise RuntimeError("DATA_ENCRYPTION_KEY must be URL-safe base64") from exc
        if len(key) != 32:
            raise RuntimeError("DATA_ENCRYPTION_KEY must decode to exactly 32 bytes")
        return key
    if get_settings().environment == "production":
        raise RuntimeError("DATA_ENCRYPTION_KEY is required in production")
    return hashlib.sha256(b"mujeeb-development-encryption-key").digest()


def encrypt_text(value: str) -> str:
    nonce = os.urandom(12)
    ciphertext = AESGCM(_key()).encrypt(nonce, value.encode(), b"mujeeb-pii-v1")
    return base64.urlsafe_b64encode(nonce + ciphertext).decode()


def decrypt_text(value: str) -> str:
    payload = base64.urlsafe_b64decode(value)
    return AESGCM(_key()).decrypt(payload[:12], payload[12:], b"mujeeb-pii-v1").decode()


def stable_hash(value: str) -> str:
    return hashlib.sha256(value.strip().lower().encode()).hexdigest()
