# from copy import deepcopy


import asyncio

from strands.hooks import HookProvider, HookRegistry, MessageAddedEvent
from strands.session import S3SessionManager
from strands.types.session import Message

from src.config import settings
from src.context.request_context import RequestContext
from src.sensitive_data_handler.data_handler_service import SensitiveDataMaskingService


class SensitiveDataMaskingHook(HookProvider):
    def __init__(
        self, session_manager: S3SessionManager, request_context: RequestContext
    ) -> None:
        self.session_manager = session_manager
        self.data_masking_service = SensitiveDataMaskingService(
            settings.SENSITIVE_DATA_HANDLER.ANALYZER,
            settings.SENSITIVE_DATA_HANDLER.ANONYMIZER,
        )
        self.context = request_context

    def register_hooks(self, registry: HookRegistry, **_) -> None:
        registry.add_callback(MessageAddedEvent, self._before_message_added_sync)

    def _before_message_added_sync(self, event: MessageAddedEvent) -> None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            task = loop.create_task(self._before_message_added(event))
            # task.add_done_callback(self._log_task_exception)
        else:
            asyncio.run(self._before_message_added(event))

    async def _before_message_added(self, event: MessageAddedEvent) -> None:
        if settings.SENSITIVE_DATA_HANDLER.MASK_SENSITIVE_DATA:
            masked_message_dict = await self.data_masking_service.process_data(
                event.message, self.context
            )
            event.message.clear()
            event.message.update(masked_message_dict)

            self.session_manager.redact_latest_message(
                redact_message=Message(**masked_message_dict), agent=event.agent
            )
