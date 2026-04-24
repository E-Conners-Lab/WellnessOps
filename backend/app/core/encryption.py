"""
Application-level PII encryption using AES-256-GCM.
Encrypts sensitive client fields before database storage.
Decrypts on read. Key loaded from environment (SEC-12).

Each encrypted value includes a random 12-byte nonce prepended to the ciphertext,
so identical plaintext produces different ciphertext every time.
"""

import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import settings

_cipher: AESGCM | None = None


def _get_cipher() -> AESGCM:
    """Lazily initialize the AES-256-GCM cipher from the configured key."""
    global _cipher
    if _cipher is not None:
        return _cipher

    key_b64 = settings.pii_encryption_key
    if not key_b64:
        raise RuntimeError(
            "PII_ENCRYPTION_KEY is not set. Generate one with: "
            "python -c \"import os, base64; print(base64.urlsafe_b64encode(os.urandom(32)).decode())\""
        )

    key_bytes = base64.urlsafe_b64decode(key_b64)
    if len(key_bytes) != 32:
        raise RuntimeError("PII_ENCRYPTION_KEY must decode to exactly 32 bytes (AES-256)")

    _cipher = AESGCM(key_bytes)
    return _cipher


def encrypt_pii(plaintext: str | None) -> str | None:
    """Encrypt a PII string. Returns base64-encoded nonce+ciphertext, or None if input is None."""
    if plaintext is None:
        return None

    cipher = _get_cipher()
    nonce = os.urandom(12)
    ciphertext = cipher.encrypt(nonce, plaintext.encode("utf-8"), None)
    # Prepend nonce to ciphertext, base64-encode the whole thing
    return base64.urlsafe_b64encode(nonce + ciphertext).decode("ascii")


def decrypt_pii(encrypted: str | None) -> str | None:
    """Decrypt a PII string. Accepts base64-encoded nonce+ciphertext, or None."""
    if encrypted is None:
        return None

    cipher = _get_cipher()
    raw = base64.urlsafe_b64decode(encrypted)
    nonce = raw[:12]
    ciphertext = raw[12:]
    plaintext_bytes = cipher.decrypt(nonce, ciphertext, None)
    return plaintext_bytes.decode("utf-8")
