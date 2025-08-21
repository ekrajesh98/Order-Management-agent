from uuid import uuid4

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from strands.experimental.hooks.events import (
    AfterModelInvocationEvent,
    BeforeModelInvocationEvent,
)
from strands.hooks import HookProvider, HookRegistry


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


class SimplePIIMaskHooks(HookProvider):
    def __init__(self):
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
        # the same operators you already defined:
        self.operators = {
            "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "EMAIL_ADDRESS"}),
            "PHONE_NUMBER": OperatorConfig("replace", {"new_value": "NUMBER"}),
            "PERSON": OperatorConfig("replace", {"new_value": "NAME"}),
            "PRODUCT_NAME": OperatorConfig("replace", {"new_value": "PRODUCT"}),
            "NAME": OperatorConfig("replace", {"new_value": "NAME"}),
        }
        # mapping session_id → {token: original_text}
        self.token_store: dict[str, dict[str, str]] = {}
        self.session_mappings = {}

    def register_hooks(self, registry: HookRegistry):
        registry.add_callback(BeforeModelInvocationEvent, self.on_before)
        registry.add_callback(AfterModelInvocationEvent, self.on_after)

    def _get_session_id(self, agent):
        return str(getattr(agent, "session_id", "default"))

    def _mask_text(self, text: str, session_id: str) -> str:
        results = self.analyzer.analyze(
            text=text, entities=list(self.operators), language="en"
        )
        if not results:
            return text

        # Prepare a fresh operators mapping with tokens that include UUIDs
        dynamic_ops = {}
        for entity in {r.entity_type for r in results}:
            base = self.operators[entity].params["new_value"]
            token = f"[{base}-{uuid4()}]"
            dynamic_ops[entity] = OperatorConfig("replace", {"new_value": token})
            # store mapping for unmasking
            self.session_mappings.setdefault(session_id, {})[token] = (
                None  # placeholder
            )

        # Perform anonymization with these dynamic operators
        anonymized = self.anonymizer.anonymize(
            text=text, analyzer_results=results, operators=dynamic_ops
        ).text

        # Now fill in original values
        for result in results:
            original = text[result.start : result.end]
            base = self.operators[result.entity_type].params["new_value"]
            # find token we created for this entity
            token = next(
                t
                for t in self.session_mappings[session_id]
                if t.startswith(f"[{base}-")
            )
            self.session_mappings[session_id][token] = original

        return anonymized

    def _unmask_text(self, text: str, session_id: str) -> str:
        """Unmask text by replacing masked tokens with original values"""
        print("\n")
        print(
            f"========session mappings: {self.session_mappings.get(session_id)}========"
        )
        if session_id not in self.session_mappings:
            return text

        unmasked_text = text
        for masked_token, original_value in self.session_mappings[session_id].items():
            if original_value:
                unmasked_text = unmasked_text.replace(masked_token, original_value)

        return unmasked_text

    def on_before(self, event: BeforeModelInvocationEvent):
        print("==========checking for PII in user messages==========")
        session = self._get_session_id(event.agent)
        for msg in event.agent.messages:
            for block in msg.get("content", []):
                if "text" in block:
                    block["text"] = self._mask_text(block["text"], session)
                if "toolResult" in block:
                    for tr in block["toolResult"]["content"]:
                        print(f"making data for : {tr["text"]}")
                        tr["text"] = self._mask_text(tr["text"], session)

    def on_after(self, event: AfterModelInvocationEvent):
        session = self._get_session_id(event.agent)
        resp = event.stop_response
        if resp and "content" in resp.message:
            for block in resp.message["content"]:
                if "text" in block:
                    block["text"] = self._mask_text(block["text"], session)
