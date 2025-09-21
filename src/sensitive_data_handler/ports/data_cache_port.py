from abc import ABC, abstractmethod
from typing import List


class SensitiveDataCacheABC(ABC):
    """
    Abstract base class defining an interface for a cache that maps
    redacted strings to their original, unredacted values.
    """

    @abstractmethod
    async def set(self, key: str, value: str, ttl: int | None = None) -> None:
        """
        Store the mapping from a redacted string (key) to its original text (value).

        Args:
            key: The redacted string.
            value: The original unredacted text.
            ttl: Optional time‐to‐live in seconds for this entry. If None, entry does not expire.
        """

    @abstractmethod
    async def get(self, key: str) -> str | None:
        """
        Retrieve the original text for a given redacted string.

        Args:
            key: The redacted string.
        Returns:
            The original unredacted text, or None if not found or expired.
        """

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Delete a mapping from the cache.

        Args:
            key: The redacted string to remove.
        Returns:
            True if the entry was found and deleted, False otherwise.
        """

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Check whether a redacted string exists in the cache.

        Args:
            key: The redacted string to check.
        Returns:
            True if an unexpired entry exists for this key, False otherwise.
        """

    @abstractmethod
    async def keys(self, pattern: str | None = None) -> List[str]:
        """
        List all redacted‐string keys currently stored in the cache.

        Args:
            pattern: Optional glob pattern to filter keys.
        Returns:
            A list of matching keys.
        """

    @abstractmethod
    async def clear(self) -> None:
        """
        Remove all entries from the cache.
        """

    @abstractmethod
    async def set_many_under(
        self, parent_key, kv: dict[str, str], ttl: int = 28_800
    ) -> None:
        """
        Store multiple key-value pairs under a common parent key.

        Args:
            parent_key: The common prefix for all keys.
            kv: A dictionary of redacted strings to original texts.
            ttl: Optional time‐to‐live in seconds for these entries. If None, entries do not expire.
        """
