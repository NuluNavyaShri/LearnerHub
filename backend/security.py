import hashlib
import os


def hash_password(password: str) -> str:
    salt = os.environ.get("LEARNHUB_SALT", "learnhub_static_salt_v1")
    return hashlib.sha256((salt + password).encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash
