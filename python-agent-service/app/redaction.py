import re
from copy import deepcopy
from typing import Any

from app.models import RedactionEvent

REDACTED = "[REDACTED]"

_SENSITIVE_KEYS = {
    "apikey",
    "authorization",
    "password",
    "passwd",
    "secret",
    "token",
    "credential",
    "credentials",
    "email",
    "phone",
    "phonenumber",
    "accesstoken",
    "refreshtoken",
    "dbpassword",
    "dbcredential",
    "dbcredentials",
    "databasepassword",
    "databasecredential",
    "databasecredentials",
    "openaikey",
    "openaiapikey",
}
_VALUE_PATTERNS = [
    ("openai_api_key", re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b")),
    ("bearer_token", re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]+", re.IGNORECASE)),
    (
        "email",
        re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    ),
    (
        "phone",
        re.compile(r"(?<!\w)(?:\+?1[- .]?)?\(?[2-9]\d{2}\)?[- .]\d{3}[- .]\d{4}(?!\w)"),
    ),
    (
        "phone",
        re.compile(r"(?<!\w)(?:\+82[- ]?)?0?1[016789][- ]?\d{3,4}[- ]?\d{4}(?!\w)"),
    ),
]


def redact(value: Any) -> tuple[Any, list[RedactionEvent]]:
    events: list[RedactionEvent] = []
    cleaned = _redact_value(deepcopy(value), "$", events)
    return cleaned, events


def _redact_value(value: Any, path: str, events: list[RedactionEvent]) -> Any:
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, nested in value.items():
            nested_path = f"{path}.{key}"
            if _is_sensitive_key(str(key)):
                result[key] = REDACTED
                events.append(RedactionEvent(path=nested_path, reason="sensitive_key"))
            else:
                result[key] = _redact_value(nested, nested_path, events)
        return result

    if isinstance(value, list):
        return [
            _redact_value(item, f"{path}[{index}]", events)
            for index, item in enumerate(value)
        ]

    if isinstance(value, str):
        cleaned = value
        reasons: list[str] = []
        for reason, pattern in _VALUE_PATTERNS:
            updated, replacements = pattern.subn(REDACTED, cleaned)
            if replacements:
                reasons.append(reason)
                cleaned = updated
        if reasons:
            events.append(RedactionEvent(path=path, reason=",".join(sorted(set(reasons)))))
        return cleaned

    return value


def _is_sensitive_key(key: str) -> bool:
    normalized = re.sub(r"[^a-z0-9]", "", key.lower())
    return normalized in _SENSITIVE_KEYS
