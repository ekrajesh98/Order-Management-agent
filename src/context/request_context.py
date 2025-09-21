from typing import Dict


class RequestContext:
    def __init__(self) -> None:
        self.sensitive_key_value: Dict[str, str] = {}
