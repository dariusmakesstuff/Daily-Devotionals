from __future__ import annotations

import base64
import hashlib
import os

from cryptography.fernet import Fernet


def _derive_fernet_key(raw: str) -> bytes:
    digest = hashlib.sha256(raw.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def get_fernet(secret_key: str | None) -> Fernet | None:
    if not secret_key:
        return None
    raw = secret_key.strip()
    if raw.startswith("base64:"):
        key = raw[7:].strip().encode("ascii")
    else:
        key = _derive_fernet_key(raw)
    return Fernet(key)


def encrypt_secret(fernet: Fernet, plaintext: str) -> str:
    return fernet.encrypt(plaintext.encode("utf-8")).decode("ascii")


def decrypt_secret(fernet: Fernet, ciphertext: str) -> str:
    return fernet.decrypt(ciphertext.encode("ascii")).decode("utf-8")


def random_secret_suggestion() -> str:
    return base64.urlsafe_b64encode(os.urandom(32)).decode("ascii")
