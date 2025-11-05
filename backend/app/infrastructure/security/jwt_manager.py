"""
JWT (JSON Web Token) manager for session tokens.

Handles creation, validation, and decoding of JWT tokens
for secure session management.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Optional

import jwt

from app.core.exceptions import InvalidTokenError, SessionExpiredError

logger = logging.getLogger(__name__)


class JWTManager:
    """
    JWT token manager.

    Provides:
    - Token creation with expiration
    - Token validation and decoding
    - Automatic expiration checking
    - Claims management

    Security notes:
    - Uses HS256 algorithm (HMAC with SHA-256)
    - Tokens include expiration (exp) and issued-at (iat) claims
    - Secret key is never exposed in tokens
    - Tokens are stateless (server doesn't store them)
    """

    # JWT configuration
    ALGORITHM = "HS256"
    TOKEN_TYPE = "Bearer"

    def __init__(self, secret_key: str, default_expiration: int = 1800):
        """
        Initialize JWT manager.

        Args:
            secret_key: Secret key for signing tokens (32+ chars recommended)
            default_expiration: Default token expiration in seconds (default 30min)

        Raises:
            ValueError: If secret key is too short
        """
        if len(secret_key) < 32:
            raise ValueError("Secret key must be at least 32 characters")

        self.secret_key = secret_key
        self.default_expiration = default_expiration

        logger.info(
            f"JWT manager initialized (default expiration: {default_expiration}s)"
        )

    def create_token(
        self,
        subject: str,
        claims: Optional[dict[str, Any]] = None,
        expiration: Optional[int] = None,
    ) -> str:
        """
        Create a JWT token.

        Args:
            subject: Token subject (e.g., session_id, user_id)
            claims: Additional claims to include in token
            expiration: Custom expiration in seconds (None = use default)

        Returns:
            Encoded JWT token

        Example:
            token = manager.create_token(
                subject="session_abc123",
                claims={"database": "/path/to/db.kdbx"},
                expiration=3600
            )
        """
        now = datetime.utcnow()
        exp_seconds = expiration or self.default_expiration
        exp_time = now + timedelta(seconds=exp_seconds)

        # Build payload
        payload = {
            "sub": subject,  # Subject (session_id)
            "iat": now,  # Issued at
            "exp": exp_time,  # Expiration
            "type": self.TOKEN_TYPE,  # Token type
        }

        # Add custom claims
        if claims:
            # Filter out sensitive data
            safe_claims = {
                k: v for k, v in claims.items() if not self._is_sensitive_claim(k)
            }
            payload.update(safe_claims)

        try:
            token = jwt.encode(payload, self.secret_key, algorithm=self.ALGORITHM)

            logger.debug(
                f"JWT token created for subject: {subject[:8]}... "
                f"(expires in {exp_seconds}s)"
            )

            return token

        except Exception as e:
            logger.error(f"Failed to create JWT token: {str(e)}")
            raise

    def decode_token(self, token: str, verify_expiration: bool = True) -> dict[str, Any]:
        """
        Decode and validate a JWT token.

        Args:
            token: JWT token to decode
            verify_expiration: Check if token is expired (default True)

        Returns:
            Token payload (claims)

        Raises:
            InvalidTokenError: If token is invalid or malformed
            SessionExpiredError: If token is expired (and verify_expiration=True)
        """
        try:
            # Decode and verify token
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.ALGORITHM],
                options={"verify_exp": verify_expiration},
            )

            logger.debug(f"JWT token decoded successfully for subject: {payload.get('sub', 'unknown')[:8]}...")

            return payload

        except jwt.ExpiredSignatureError as e:
            logger.warning("Token expired")
            raise SessionExpiredError("Token has expired") from e

        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid token: {str(e)}")
            raise InvalidTokenError(f"Invalid token: {str(e)}") from e

        except Exception as e:
            logger.error(f"Token decoding failed: {str(e)}")
            raise InvalidTokenError(f"Token decoding failed: {str(e)}") from e

    def verify_token(self, token: str) -> bool:
        """
        Verify if a token is valid.

        Args:
            token: JWT token to verify

        Returns:
            True if valid, False otherwise
        """
        try:
            self.decode_token(token, verify_expiration=True)
            return True
        except (InvalidTokenError, SessionExpiredError):
            return False

    def get_subject(self, token: str) -> Optional[str]:
        """
        Get the subject (sub claim) from a token.

        Args:
            token: JWT token

        Returns:
            Subject string or None if invalid
        """
        try:
            payload = self.decode_token(token, verify_expiration=True)
            return payload.get("sub")
        except (InvalidTokenError, SessionExpiredError):
            return None

    def get_expiration(self, token: str) -> Optional[datetime]:
        """
        Get the expiration time of a token.

        Args:
            token: JWT token

        Returns:
            Expiration datetime or None if invalid
        """
        try:
            payload = self.decode_token(token, verify_expiration=False)
            exp_timestamp = payload.get("exp")

            if exp_timestamp:
                return datetime.fromtimestamp(exp_timestamp)

            return None

        except (InvalidTokenError, SessionExpiredError):
            return None

    def get_remaining_time(self, token: str) -> Optional[int]:
        """
        Get remaining time until token expires.

        Args:
            token: JWT token

        Returns:
            Remaining seconds or None if expired/invalid
        """
        exp_time = self.get_expiration(token)

        if exp_time:
            remaining = (exp_time - datetime.utcnow()).total_seconds()
            return max(0, int(remaining))

        return None

    def refresh_token(
        self,
        token: str,
        expiration: Optional[int] = None,
    ) -> str:
        """
        Refresh a token (issue a new one with extended expiration).

        Args:
            token: Existing token to refresh
            expiration: New expiration in seconds (None = use default)

        Returns:
            New JWT token

        Raises:
            InvalidTokenError: If original token is invalid
            SessionExpiredError: If original token is expired

        Note:
            This creates a completely new token with new issued-at time.
        """
        # Decode existing token (verify it's valid but don't check expiration)
        try:
            payload = self.decode_token(token, verify_expiration=False)
        except InvalidTokenError:
            raise

        # Extract subject and custom claims
        subject = payload.get("sub")
        if not subject:
            raise InvalidTokenError("Token missing subject claim")

        # Extract custom claims (exclude standard JWT claims)
        standard_claims = {"sub", "iat", "exp", "type", "nbf", "iss", "aud", "jti"}
        custom_claims = {
            k: v for k, v in payload.items() if k not in standard_claims
        }

        # Create new token
        new_token = self.create_token(
            subject=subject,
            claims=custom_claims,
            expiration=expiration,
        )

        logger.info(f"Token refreshed for subject: {subject[:8]}...")

        return new_token

    @staticmethod
    def _is_sensitive_claim(claim_name: str) -> bool:
        """
        Check if a claim name contains sensitive data.

        Args:
            claim_name: Claim name to check

        Returns:
            True if sensitive, False otherwise
        """
        sensitive_keywords = [
            "password",
            "passwd",
            "pwd",
            "secret",
            "token",
            "key",
            "private",
            "credential",
        ]

        claim_lower = claim_name.lower()
        return any(keyword in claim_lower for keyword in sensitive_keywords)

    def extract_bearer_token(self, authorization_header: str) -> Optional[str]:
        """
        Extract token from Authorization header.

        Args:
            authorization_header: Authorization header value

        Returns:
            Token or None if invalid format

        Example:
            "Bearer eyJ0eXAiOiJKV1..." -> "eyJ0eXAiOiJKV1..."
        """
        if not authorization_header:
            return None

        parts = authorization_header.split()

        if len(parts) != 2:
            return None

        scheme, token = parts

        if scheme.lower() != "bearer":
            return None

        return token
