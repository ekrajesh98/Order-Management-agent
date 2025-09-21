from abc import ABC, abstractmethod

from src.models.pydantic import AnalyzerResult


class SensitiveDataAnalyzerABC(ABC):
    """
    Abstract base class for sensitive data analyzers.

    This class defines the interface for any service that detects sensitive
    or personally identifiable information (PII) in text. Implementations
    may use different underlying libraries or APIs (e.g., Presidio, custom
    ML models, third-party services), but they must expose a consistent
    `analyze` method.

    Using this abstraction allows switching between different analyzer
    implementations without changing the service layer code.
    """

    @abstractmethod
    async def analyze(
        self, text: str, entities_to_scan: list[str] = []
    ) -> list[AnalyzerResult]:
        """
        Analyze the given text and return information about detected
        sensitive data.

        Args:
            text: The input text to analyze.
            entities_to_scan: Optional list of entity types to specifically
                look for (e.g., ["EMAIL_ADDRESS", "PHONE_NUMBER"]). If empty,
                the analyzer's default set of entities will be used.

        Returns:

        """
