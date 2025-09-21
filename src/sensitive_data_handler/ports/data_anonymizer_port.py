from abc import ABC, abstractmethod

from src.models.pydantic import AnalyzerResult, AnonymizerResult


class SensitiveDataAnonymizerABC(ABC):
    """
    Abstract base class for sensitive data anonymizers.

    This class defines the contract for anonymizing sensitive data
    within a given text. Implementations of this class should take
    an input string, identify sensitive information (such as PII), and
    return a modified string where the sensitive data has been masked.
    """

    @abstractmethod
    async def anonymize(
        self, text: str, analyzer_results: list[AnalyzerResult]
    ) -> AnonymizerResult:
        """
        Anonymize sensitive data in the given text.

        Implementations should detect sensitive information
        (such as names, phone numbers, email addresses) and apply
        the appropriate anonymization or masking techniques before
        returning the result.

        Args:
            text: The input text containing potentially sensitive data.
            analyzer_results: List of AnalyzerResult objects indicating
                the locations and types of sensitive data detected in the text.

        Returns:
            AnonymizerResult
        """
