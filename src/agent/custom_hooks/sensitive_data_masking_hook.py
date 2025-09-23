# from copy import deepcopy


import asyncio

from strands.hooks import HookProvider, HookRegistry, MessageAddedEvent
from strands.session import S3SessionManager

from src.config import settings
from src.context.request_context import RequestContext
from src.sensitive_data_handler.data_handler_service import SensitiveDataMaskingService


class SensitiveDataMaskingHook(HookProvider):
    def __init__(
        self,
        session_manager: S3SessionManager,
        request_context: RequestContext,
        session_id: str,
    ) -> None:
        self.session_manager = session_manager
        self.data_masking_service = SensitiveDataMaskingService(
            settings.SENSITIVE_DATA_HANDLER.ANALYZER,
            settings.SENSITIVE_DATA_HANDLER.ANONYMIZER,
        )
        self.context = request_context
        self.session_id = session_id

    def register_hooks(self, registry: HookRegistry, **_) -> None:
        registry.add_callback(MessageAddedEvent, self._before_message_added_sync)

    def _before_message_added_sync(self, event: MessageAddedEvent) -> None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            loop.create_task(self._before_message_added(event))
        else:
            asyncio.run(self._before_message_added(event))

    async def _before_message_added(self, event: MessageAddedEvent) -> None:
        if settings.SENSITIVE_DATA_HANDLER.MASK_SENSITIVE_DATA:
            masked_message_dict = await self.data_masking_service.process_data(
                event.message, self.context
            )
            event.message.clear()
            event.message.update(masked_message_dict)

            self.session_manager.update_message(
                self.session_id,
                event.agent.agent_id,
                self.session_manager._latest_agent_message[event.agent.agent_id],
            )
