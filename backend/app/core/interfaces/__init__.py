"""
Port interfaces (Hexagonal Architecture).

These interfaces define the contracts that infrastructure adapters must implement:
- IKeePassXCRepository: Database operations via keepassxc-cli
- ICacheService: Caching operations (Redis, Memory)
- ISecurityService: Security operations (sessions, encryption, validation)
"""

from app.core.interfaces.cache import ICacheService
from app.core.interfaces.repository import IKeePassXCRepository
from app.core.interfaces.security import ISecurityService

__all__ = [
    "ICacheService",
    "IKeePassXCRepository",
    "ISecurityService",
]
