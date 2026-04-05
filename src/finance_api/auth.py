from __future__ import annotations

from hashlib import pbkdf2_hmac
import hmac
import os
import secrets


PBKDF2_ITERATIONS = 210_000


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    algorithm, iterations, salt_hex, digest_hex = stored_hash.split("$", maxsplit=3)
    if algorithm != "pbkdf2_sha256":
        return False
    digest = pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt_hex),
        int(iterations),
    )
    return hmac.compare_digest(digest.hex(), digest_hex)


def generate_token() -> str:
    return secrets.token_urlsafe(32)

