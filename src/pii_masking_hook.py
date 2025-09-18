# secure_masking_hook.py
import uuid

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from strands.experimental.hooks import (
    AfterModelInvocationEvent,
    AfterToolInvocationEvent,
    BeforeModelInvocationEvent,
)
from strands.hooks import (
    HookProvider,
    HookRegistry,
    MessageAddedEvent,
)


class DebuggingHook(HookProvider):
    def register_hooks(self, registry: HookRegistry):
        registry.add_callback(BeforeModelInvocationEvent, self.on_before_model)
        registry.add_callback(AfterModelInvocationEvent, self.on_after_model)

    def on_before_model(self, event: BeforeModelInvocationEvent):
        print(
            "\033[31m======================>>> About to invoke LLM with messages <<<<<<<<<<<======================\033[0m"
        )
        for message in event.agent.messages:
            for result in message.get("content", [{}]):
                print(f"User message: {result.get('text', '')}")
                if result.get("toolResult"):
                    tool_result = result["toolResult"]
                    tool_result_content = tool_result.get("content", [{}])
                    if tool_result_content:
                        print(tool_result.get("content", [{}])[0].get("text", ""))
        print(
            "\033[92m============>>>> LLM response <<<<<<<<======================\033[0m"
        )

    def on_after_model(self, event: AfterModelInvocationEvent):
        if event.stop_response:
            pass
        else:
            print("No response from LLM or invocation failed")


class MaskingHook(HookProvider):
    def __init__(self):
        self.operators = [
            "EMAIL_ADDRESS",
            "PERSON",
            "NAME",
            "PHONE_NUMBER",
            "PRODUCT_NAME",
            "LOCATION",
            "ADDRESS",
        ]

    def register_hooks(self, registry: HookRegistry) -> None:
        # registry.add_callback(BeforeModelInvocationEvent, self.before_invocation)
        registry.add_callback(MessageAddedEvent, self.on_message_added)
        registry.add_callback(AfterToolInvocationEvent, self.after_tool_invocation)

    def before_invocation(self, event: BeforeModelInvocationEvent):
        print(f"==========messages: {event.agent.messages}")
        raw_text = event.agent.messages[0].get("content", [{}])[0].get("text", "")

        validated_and_masked_text = self._validate_and_mask_sensitive_data(raw_text)

        if hasattr(event, "input"):
            event.input = validated_and_masked_text
        elif hasattr(event, "request") and isinstance(event.request, dict):
            event.request["input"] = validated_and_masked_text
        else:
            setattr(event, "input", validated_and_masked_text)

    def on_message_added(self, event: MessageAddedEvent):
        msg = getattr(event, "message", None)
        if not msg:
            return
        text = getattr(msg, "text", None) or msg.get("text")

        if text:
            validated_and_masked_text = self._validate_and_mask_sensitive_data(text)

            if hasattr(msg, "text"):
                msg.text = validated_and_masked_text
            else:
                msg["text"] = validated_and_masked_text

    def after_tool_invocation(self, event: AfterToolInvocationEvent):
        # tool_result = getattr(event, "tool_result", None) or event.tool_result
        # if not tool_result:
        #     return
        # text = getattr(tool_result, "text", None) or tool_result.get("text")

        # if text:
        #     validated_and_masked_text = self._validate_and_mask_sensitive_data(text)

        #     if hasattr(tool_result, "text"):
        #         tool_result.text = validated_and_masked_text
        #     else:
        #         tool_result["text"] = validated_and_masked_text
        print(f"=========tool result: {event.result}=========")

    def _validate_and_mask_sensitive_data(self, text: str) -> str:
        if not text:
            return text

        pii_data = {}

        analyzer = AnalyzerEngine()

        analyzer_result = analyzer.analyze(
            text=text,
            language="en",
            entities=self.operators,
            correlation_id=uuid.uuid4(),
            score_threshold=0.7,
        )
        for res in analyzer_result:
            res.entity_type = self._get_new_name_for_entity(res.entity_type)
            pii_data[res.entity_type] = text[res.start : res.end]

        engine = AnonymizerEngine()
        result = engine.anonymize(
            text=text,
            analyzer_results=analyzer_result,
        )

        return result.text

    def _get_new_name_for_entity(self, entity: str) -> str:
        if entity in self.operators:
            return f"{entity}_{uuid.uuid4()}"
        else:
            return entity
