import hashlib
import uuid

# from copy import deepcopy
from typing import Any

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from strands.hooks import HookProvider, HookRegistry, MessageAddedEvent
from strands.session import FileSessionManager
from strands.types.session import Message


class PIIMaskingService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            obj = super().__new__(cls)
            obj.analyzer = AnalyzerEngine()
            obj.anonymizer = AnonymizerEngine()
            obj.operators = [
                "EMAIL_ADDRESS",
                "PERSON",
                "NAME",
                "PHONE_NUMBER",
                "PRODUCT_NAME",
                "LOCATION",
                "ADDRESS",
            ]
            obj.keys_to_ignore = ["toolUseId", "status", "message_id", "role"]
            cls._instance = obj
        return cls._instance

    def _stable_redaction_key(self, entity_type: str, original: str) -> str:
        digest = hashlib.sha256(original.encode("utf-8")).hexdigest()[:8]
        return f"{entity_type}_{digest}"

    def _get_new_name_for_entity(self, entity: str, text: str = "") -> str:
        if entity in self.operators:
            return self._stable_redaction_key(entity, text)
        else:
            return entity

    def validate_and_mask_text(
        self,
        text: str,
    ) -> str:
        """Mask PII in the given text using Presidio"""
        if not text:
            return text

        analyzer_result = self.analyzer.analyze(
            text=text,
            language="en",
            entities=self.operators,
            correlation_id=uuid.uuid4(),
            score_threshold=0.7,
        )
        for res in analyzer_result:
            pii_text = text[res.start : res.end]
            res.entity_type = self._get_new_name_for_entity(res.entity_type, pii_text)

        result = self.anonymizer.anonymize(
            text=text,
            analyzer_results=analyzer_result,
        )

        return result.text

    def validate_and_mask_json(
        self,
        obj: Any,
        parent_key: str = None,
    ) -> Any:
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
                    result[k] = self.validate_and_mask_json(v, k)
            return result

        if isinstance(obj, list):
            return [self.validate_and_mask_json(item, parent_key) for item in obj]

        if isinstance(obj, str):
            if parent_key and parent_key in self.keys_to_ignore:
                return obj
            return self.validate_and_mask_text(obj)

        return obj


class PiiMaskingHook(HookProvider):
    def __init__(self, session_manager: FileSessionManager):
        self.session_manager = session_manager
        self.pii_masking_service = PIIMaskingService()

    def register_hooks(self, registry: HookRegistry, **_):
        registry.add_callback(MessageAddedEvent, self._before_message_added)

    def _before_message_added(self, event: MessageAddedEvent):
        masked_message_dict = self.pii_masking_service.validate_and_mask_json(
            event.message
        )
        event.message.clear()
        event.message.update(masked_message_dict)

        self.session_manager.redact_latest_message(
            redact_message=Message(**masked_message_dict), agent=event.agent
        )
