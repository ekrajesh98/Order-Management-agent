import hashlib

from src.models.pydantic import AnalyzerResult
from src.sensitive_data_handler.adapters.presidio_analyzer import PresidioAnalyzer
from src.sensitive_data_handler.adapters.presidio_anonymizer import PresidioAnonymizer
from src.sensitive_data_handler.ports.data_analyzer_port import SensitiveDataAnalyzerABC
from src.sensitive_data_handler.ports.data_anonymizer_port import (
    SensitiveDataAnonymizerABC,
)


class SensitiveDataHandlerService:
    def __init__(self) -> None:
        self.analyzer: SensitiveDataAnalyzerABC = PresidioAnalyzer()
        self.anonymizer: SensitiveDataAnonymizerABC = PresidioAnonymizer()
        self.keys_to_ignore = ["toolUseId", "status", "message_id", "role"]
        self.masked_key_value = {}

    def process_data(
        self,
        data: str | dict | list,
    ) -> str:
        result = self._process_data_recursively(data)
        return result

    def _process_data_recursively(
        self,
        obj: str | dict | list,
        parent_key: str = None,
    ) -> str | dict | list:
        """
        Recursively walk through `obj`. For:
          - dict: return a new dict with each value masked
          - list: return a new list with each element masked
          - string: mask PII
          - other: return unchanged
        """
        if isinstance(obj, dict):
            result = {}
            for k, v in obj.items():
                if k in self.keys_to_ignore:
                    result[k] = v
                else:
                    result[k] = self._process_data_recursively(v, k)
            return result

        if isinstance(obj, list):
            return [self._process_data_recursively(item, parent_key) for item in obj]

        if isinstance(obj, str):
            if parent_key and parent_key in self.keys_to_ignore:
                return obj

            if obj:
                analyzer_result = self._analyse_text(obj)

                for res in analyzer_result:
                    sensitive_text = obj[res.start : res.end]
                    res.entity_type = self._get_new_name_for_entity(
                        res.entity_type, sensitive_text
                    )
                    self.masked_key_value[res.entity_type] = sensitive_text

                return self._anonymize_text(obj, analyzer_result)

        return obj

    def _analyse_text(self, text: str) -> list[AnalyzerResult]:
        analyzer_result = self.analyzer.analyze(text=text)

        return analyzer_result

    def _anonymize_text(self, text: str, analyzer_result: AnalyzerResult) -> str:
        anonymizer_result = self.anonymizer.anonymize(
            text=text,
            analyzer_results=analyzer_result,
        )
        return anonymizer_result.text

    def _stable_redaction_key(self, entity_type: str, original: str) -> str:
        digest = hashlib.sha256(original.encode("utf-8")).hexdigest()[:8]
        return f"{entity_type}_{digest}"

    def _get_new_name_for_entity(self, entity: str, text: str = "") -> str:
        return self._stable_redaction_key(entity, text)
