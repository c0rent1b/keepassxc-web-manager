"""
KeePassXC infrastructure layer.

This module provides the infrastructure implementation for interacting
with KeePassXC databases via keepassxc-cli.

Components:
- KeePassXCCLIWrapper: Async wrapper for CLI operations
- KeePassXCCommandBuilder: Command construction with security
- KeePassXCOutputParser: Parse CLI output into domain entities
- KeePassXCRepository: Repository implementation (IKeePassXCRepository adapter)
"""

from app.infrastructure.keepassxc.cli_wrapper import KeePassXCCLIWrapper
from app.infrastructure.keepassxc.command_builder import KeePassXCCommandBuilder
from app.infrastructure.keepassxc.output_parser import KeePassXCOutputParser
from app.infrastructure.keepassxc.repository import KeePassXCRepository

__all__ = [
    "KeePassXCCLIWrapper",
    "KeePassXCCommandBuilder",
    "KeePassXCOutputParser",
    "KeePassXCRepository",
]
