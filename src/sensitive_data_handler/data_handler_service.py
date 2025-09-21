import hashlib
import re
from typing import Any, overload

from src.context.request_context import RequestContext
from src.models.pydantic import AnalyzerResult
from src.sensitive_data_handler.ports.data_analyzer_port import SensitiveDataAnalyzerABC
from src.sensitive_data_handler.ports.data_anonymizer_port import (
    SensitiveDataAnonymizerABC,
)
from src.sensitive_data_handler.ports.data_cache_port import SensitiveDataCacheABC
from src.sensitive_data_handler.ports.data_handler_port import (
    SensitiveDataMaskerABC,
    SensitiveDataUnMaskerABC,
)


class SensitiveDataMaskingService(SensitiveDataMaskerABC):
    def __init__(
        self, analyzer: SensitiveDataAnalyzerABC, anonymizer: SensitiveDataAnonymizerABC
    ) -> None:
        self.analyzer = analyzer
        self.anonymizer = anonymizer
        self.keys_to_ignore = ["toolUseId", "status", "message_id", "role"]

    @overload
    async def process_data(self, data: str, context: RequestContext) -> str: ...
    @overload
    async def process_data(
        self, data: dict[str, Any], context: RequestContext
    ) -> dict[str, Any]: ...
    @overload
    async def process_data(
        self, data: dict[Any], context: RequestContext
    ) -> list[Any]: ...

    async def process_data(
        self, data: str | dict | list, context: RequestContext
    ) -> str | dict | list:
        """Process the input data to detect and mask sensitive information."""
        result = await self._process_data_recursively(data, context)

        return result

    async def _process_data_recursively(
        self,
        obj: str | dict | list,
        context: RequestContext,
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
                    result[k] = await self._process_data_recursively(v, context, k)
            return result

        if isinstance(obj, list):
            return [
                await self._process_data_recursively(item, context, parent_key)
                for item in obj
            ]

        if isinstance(obj, str):
            if parent_key and parent_key in self.keys_to_ignore:
                return obj

            if obj:
                analyzer_result = await self._analyse_text(obj)

                for res in analyzer_result:
                    sensitive_text = obj[res.start : res.end]
                    res.entity_type = await self._get_new_name_for_entity(
                        res.entity_type, sensitive_text
                    )
                    context.sensitive_key_value[res.entity_type] = sensitive_text

                return await self._anonymize_text(obj, analyzer_result)

        return obj

    async def _analyse_text(self, text: str) -> list[AnalyzerResult]:
        analyzer_result = await self.analyzer.analyze(text=text)

        return analyzer_result

    async def _anonymize_text(self, text: str, analyzer_result: AnalyzerResult) -> str:
        anonymizer_result = await self.anonymizer.anonymize(
            text=text,
            analyzer_results=analyzer_result,
        )
        return anonymizer_result.text

    async def _hashed_redaction_key(self, entity_type: str, original: str) -> str:
        digest = hashlib.sha256(original.encode("utf-8")).hexdigest()[:8]
        return f"{entity_type}_{digest}"

    async def _get_new_name_for_entity(self, entity: str, text: str = "") -> str:
        return await self._hashed_redaction_key(entity, text)


class SensitiveDataUnMaskingService(SensitiveDataUnMaskerABC):
    def __init__(self, cache: SensitiveDataCacheABC) -> None:
        self.cache = cache
        self._placeholder_pattern = re.compile(r"<[A-Z_]+_[0-9a-f]{8}>")

    async def process_data(
        self,
        data: str,
        cache_lookup_key: str | None = None,
        initial_kv: dict[str, str] = {},
    ) -> str:
        """
        Process the input data to unmask sensitive information.

        Args:
            data: The input string potentially containing placeholders.
            cache_lookup_key: Optional key to fetch additional mappings from the cache.
            initial_kv: Initial key-value pairs for placeholder replacement.
        Returns:
            The unmasked string with placeholders replaced by original values.
        """

        placeholders = set(self._placeholder_pattern.findall(data))
        if not placeholders:
            return data

        combined_map: dict[str, str] = dict(initial_kv)

        if cache_lookup_key:
            for ph in placeholders:
                if ph in combined_map:
                    continue

                masked_key_value_in_redis = await self.cache.get(cache_lookup_key)
                ph_key = ph[1:-1]
                original = masked_key_value_in_redis.get(ph_key)
                if original is not None:
                    combined_map[ph] = original

        def _replacer(match: re.Match) -> str:
            ph = match.group(0)
            return combined_map.get(ph, ph)

        return self._placeholder_pattern.sub(_replacer, data)
