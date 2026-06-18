from cryptography.fernet import Fernet
from app.core.config import settings

cipher_suite = Fernet(settings.DB_ENCRYPTION_KEY.encode())

# if needed to encrypt/decrypt data in the database, we can use these functions. For example, we could encrypt sensitive user info before saving it to the database, and decrypt it when retrieving it.

def encrypt_data(text: str) -> str:
    """Encrypts a plaintext string into a secure token."""
    if not text:
        return text
    return cipher_suite.encrypt(text.encode()).decode()

def decrypt_data(encrypted_text: str) -> str:
    """Decrypts a secure token back into plaintext."""
    if not encrypted_text:
        return encrypted_text
    return cipher_suite.decrypt(encrypted_text.encode()).decode()