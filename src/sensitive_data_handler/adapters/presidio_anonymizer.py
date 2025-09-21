from presidio_anonymizer import AnonymizerEngine

from src.models.pydantic import AnalyzerResult, AnonymizerResult
from src.sensitive_data_handler.ports.data_anonymizer_port import (
    SensitiveDataAnonymizerABC,
)


class PresidioAnonymizerEngine:
    _instance = None
    _anonymizer: AnonymizerEngine

    def __new__(cls):
        if cls._instance is None:
            obj = super().__new__(cls)
            obj._anonymizer = AnonymizerEngine()
            cls._instance = obj
        return cls._instance


class PresidioAnonymizer(SensitiveDataAnonymizerABC):
    def __init__(
        self,
    ) -> None:
        self._engine = PresidioAnonymizerEngine()

    async def anonymize(
        self, text: str, analyzer_results: list[AnalyzerResult]
    ) -> AnonymizerResult:
        if not text:
            return text

        redacted_text = self._engine._anonymizer.anonymize(
            text=text,
            analyzer_results=analyzer_results,
        )
        return AnonymizerResult(text=redacted_text.text)
