from abc import ABC, abstractmethod
from typing import List, Optional


class SensitiveDataCacheABC(ABC):
    """
    Abstract base class defining an interface for a cache that maps
    redacted strings to their original, unredacted values.
    """

    @abstractmethod
    def set(self, key: str, value: str, ttl: Optional[int] = None) -> None:
        """
        Store the mapping from a redacted string (key) to its original text (value).

        Args:
            key: The redacted string.
            value: The original unredacted text.
            ttl: Optional time‐to‐live in seconds for this entry. If None, entry does not expire.
        """

    @abstractmethod
    def get(self, key: str) -> Optional[str]:
        """
        Retrieve the original text for a given redacted string.

        Args:
            key: The redacted string.
        Returns:
            The original unredacted text, or None if not found or expired.
        """

    @abstractmethod
    def delete(self, key: str) -> bool:
        """
        Delete a mapping from the cache.

        Args:
            key: The redacted string to remove.
        Returns:
            True if the entry was found and deleted, False otherwise.
        """

    @abstractmethod
    def exists(self, key: str) -> bool:
        """
        Check whether a redacted string exists in the cache.

        Args:
            key: The redacted string to check.
        Returns:
            True if an unexpired entry exists for this key, False otherwise.
        """

    @abstractmethod
    def keys(self, pattern: Optional[str] = None) -> List[str]:
        """
        List all redacted‐string keys currently stored in the cache.

        Args:
            pattern: Optional glob pattern to filter keys.
        Returns:
            A list of matching keys.
        """

    @abstractmethod
    def clear(self) -> None:
        """
        Remove all entries from the cache.
        """
