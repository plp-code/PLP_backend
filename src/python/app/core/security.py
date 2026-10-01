import bcrypt


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str | None) -> bool:
    if not hashed or not plain:
        return False
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))