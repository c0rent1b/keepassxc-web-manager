"""
Encryption service using Fernet (symmetric encryption).

Fernet provides:
- Authenticated encryption (prevents tampering)
- Timestamp verification
- Key rotation support
- Secure random IV generation
"""

import base64
import logging
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

from app.core.exceptions import SecurityException

logger = logging.getLogger(__name__)


class FernetEncryptionService:
    """
    Encryption service for sensitive data.

    Uses Fernet (symmetric encryption) for encrypting passwords
    and other sensitive data in memory.

    Security notes:
    - Encryption key is derived from SECRET_KEY
    - Keys are kept in memory only, never persisted
    - Encrypted data includes timestamp for freshness checks
    - All operations are authenticated (prevents tampering)
    """

    def __init__(self, secret_key: str):
        """
        Initialize encryption service.

        Args:
            secret_key: Application secret key (must be 32+ chars)

        Raises:
            ValueError: If secret key is too short
        """
        if len(secret_key) < 32:
            raise ValueError("Secret key must be at least 32 characters")

        # Derive Fernet key from secret
        self._fernet_key = self._derive_fernet_key(secret_key)
        self._fernet = Fernet(self._fernet_key)

        logger.info("Encryption service initialized")

    @staticmethod
    def _derive_fernet_key(secret_key: str) -> bytes:
        """
        Derive a Fernet-compatible key from the secret.

        Fernet requires a 32-byte base64-encoded key.

        Args:
            secret_key: Application secret key

        Returns:
            Fernet-compatible key
        """
        # Use first 32 bytes of secret, pad if needed
        key_material = (secret_key + "0" * 32)[:32].encode()

        # Base64 encode to make it Fernet-compatible
        return base64.urlsafe_b64encode(key_material)

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext data.

        Args:
            plaintext: Data to encrypt

        Returns:
            Base64-encoded encrypted data (includes timestamp)

        Raises:
            SecurityException: If encryption fails
        """
        try:
            if not plaintext:
                raise ValueError("Cannot encrypt empty data")

            encrypted_bytes = self._fernet.encrypt(plaintext.encode())
            encrypted_str = encrypted_bytes.decode()

            logger.debug("Data encrypted successfully")
            return encrypted_str

        except Exception as e:
            logger.error(f"Encryption failed: {str(e)}")
            raise SecurityException(f"Encryption failed: {str(e)}") from e

    def decrypt(self, encrypted_data: str, max_age: Optional[int] = None) -> str:
        """
        Decrypt encrypted data.

        Args:
            encrypted_data: Base64-encoded encrypted data
            max_age: Maximum age in seconds (None = no limit)

        Returns:
            Decrypted plaintext

        Raises:
            SecurityException: If decryption fails or data is too old
        """
        try:
            if not encrypted_data:
                raise ValueError("Cannot decrypt empty data")

            decrypted_bytes = self._fernet.decrypt(
                encrypted_data.encode(),
                ttl=max_age,  # Will raise if data is older than max_age
            )
            decrypted_str = decrypted_bytes.decode()

            logger.debug("Data decrypted successfully")
            return decrypted_str

        except InvalidToken as e:
            logger.error("Decryption failed: Invalid token or expired")
            raise SecurityException("Decryption failed: Invalid or expired token") from e

        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            raise SecurityException(f"Decryption failed: {str(e)}") from e

    def encrypt_password(self, password: str) -> str:
        """
        Encrypt a password.

        This is a convenience method for password encryption.

        Args:
            password: Plain text password

        Returns:
            Encrypted password

        Raises:
            SecurityException: If encryption fails
        """
        if not password:
            raise ValueError("Password cannot be empty")

        return self.encrypt(password)

    def decrypt_password(self, encrypted_password: str, max_age: int = 3600) -> str:
        """
        Decrypt a password.

        Args:
            encrypted_password: Encrypted password
            max_age: Maximum age in seconds (default 1 hour)

        Returns:
            Decrypted password

        Raises:
            SecurityException: If decryption fails or password is too old
        """
        if not encrypted_password:
            raise ValueError("Encrypted password cannot be empty")

        return self.decrypt(encrypted_password, max_age=max_age)

    def rotate_key(self, new_secret_key: str) -> None:
        """
        Rotate encryption key.

        Warning: After rotation, old encrypted data cannot be decrypted
        unless you decrypt with old key first and re-encrypt with new key.

        Args:
            new_secret_key: New secret key

        Raises:
            ValueError: If new secret key is invalid
        """
        if len(new_secret_key) < 32:
            raise ValueError("New secret key must be at least 32 characters")

        logger.warning("Rotating encryption key - old encrypted data will be invalid")

        self._fernet_key = self._derive_fernet_key(new_secret_key)
        self._fernet = Fernet(self._fernet_key)

        logger.info("Encryption key rotated successfully")

    @staticmethod
    def generate_secret_key(length: int = 64) -> str:
        """
        Generate a new random secret key.

        Args:
            length: Key length (minimum 32)

        Returns:
            Random secret key

        Raises:
            ValueError: If length is too short
        """
        if length < 32:
            raise ValueError("Key length must be at least 32")

        # Generate random bytes
        import secrets

        return secrets.token_urlsafe(length)
