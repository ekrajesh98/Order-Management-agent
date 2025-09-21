from abc import ABC, abstractmethod
from typing import Any


class SensitiveDataMaskerABC(ABC):
    @abstractmethod
    async def process_data(self, data: str | list[Any] | dict[Any, Any]) -> str:
        """Process the input data to detect and mask sensitive information."""
        pass


class SensitiveDataUnMaskerABC(ABC):
    @abstractmethod
    async def process_data(
        self,
        data: str,
        cache_lookup_key: str | None = None,
        initial_kv: dict[str, str] = {},
    ) -> str:
        """Process the input data to unmask sensitive information."""
        pass
