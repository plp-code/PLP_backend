import bcrypt

# bcrypt only uses the first 72 bytes, and bcrypt>=5 raises ValueError past
# that instead of truncating. Measured in UTF-8 bytes, not characters.
MAX_PASSWORD_BYTES = 72


def password_too_long(password: str) -> bool:
    return len(password.encode("utf-8")) > MAX_PASSWORD_BYTES


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str | None) -> bool:
    if not hashed or not plain:
        return False
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        # Over 72 bytes (or a malformed stored hash): treat as a wrong password.
        return False
