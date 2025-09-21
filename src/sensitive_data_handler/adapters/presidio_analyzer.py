from presidio_analyzer import AnalyzerEngine

from src.models.pydantic import AnalyzerResult
from src.sensitive_data_handler.ports.data_analyzer_port import SensitiveDataAnalyzerABC


class PresidioAnalyzerEngine:
    _instance = None
    _analyzer: AnalyzerEngine

    def __new__(cls):
        if cls._instance is None:
            obj = super().__new__(cls)
            obj._analyzer = AnalyzerEngine()
            cls._instance = obj
        return cls._instance


class PresidioAnalyzer(SensitiveDataAnalyzerABC):
    def __init__(self) -> None:
        self._engine = PresidioAnalyzerEngine()
        self._entities_to_scan = [
            "EMAIL_ADDRESS",
            "PERSON",
            "NAME",
            "PHONE_NUMBER",
            "PRODUCT_NAME",
            "LOCATION",
            "ADDRESS",
        ]

    async def analyze(
        self,
        text: str,
        entities_to_scan: list[str] = [],
        score_threshold: float = 0.7,
        language="en",
    ) -> list[AnalyzerResult]:
        analyser_result = self._engine._analyzer.analyze(
            text=text,
            language=language,
            entities=self._entities_to_scan
            if not entities_to_scan
            else entities_to_scan,
            score_threshold=score_threshold,
        )

        return [
            AnalyzerResult(
                entity_type=res.entity_type, start=res.start, end=res.end, score=res.end
            )
            for res in analyser_result
        ]
