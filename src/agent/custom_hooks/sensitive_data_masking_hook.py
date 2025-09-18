# from copy import deepcopy

from strands.hooks import HookProvider, HookRegistry, MessageAddedEvent
from strands.session import S3SessionManager
from strands.types.session import Message

from src.sensitive_data_handler.data_handler_service import SensitiveDataHandlerService


class SensitiveDataMaskingHook(HookProvider):
    def __init__(self, session_manager: S3SessionManager):
        self.session_manager = session_manager
        self.data_masking_service = SensitiveDataHandlerService()

    def register_hooks(self, registry: HookRegistry, **_):
        registry.add_callback(MessageAddedEvent, self._validate_and_mask_sesitive_data)

    def _validate_and_mask_sesitive_data(self, event: MessageAddedEvent):
        masked_message_dict = self.data_masking_service.process_data(event.message)
        event.message.clear()
        event.message.update(masked_message_dict)

        self.session_manager.redact_latest_message(
            redact_message=Message(**masked_message_dict), agent=event.agent
        )
