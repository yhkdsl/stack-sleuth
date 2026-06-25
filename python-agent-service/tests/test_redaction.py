from app.redaction import redact


def test_redaction_removes_sensitive_keys_and_values_recursively() -> None:
    value = {
        "OPENAI_API_KEY": "sk-" + "a" * 32,
        "nested": {
            "authorization": "Bearer secret-access-token",
            "email": "developer@example.com",
            "phone": "+1-415-555-0100",
            "dbCredentials": {"username": "reader", "password": "secret"},
            "safe": "demo-user-42",
        },
        "message": "Contact developer@example.com with token sk-" + "b" * 32,
    }

    cleaned, events = redact(value)

    assert cleaned["OPENAI_API_KEY"] == "[REDACTED]"
    assert cleaned["nested"]["authorization"] == "[REDACTED]"
    assert cleaned["nested"]["email"] == "[REDACTED]"
    assert cleaned["nested"]["phone"] == "[REDACTED]"
    assert cleaned["nested"]["dbCredentials"] == "[REDACTED]"
    assert cleaned["nested"]["safe"] == "demo-user-42"
    assert "developer@example.com" not in cleaned["message"]
    assert "sk-" not in cleaned["message"]
    assert {event.path for event in events} >= {
        "$.OPENAI_API_KEY",
        "$.nested.authorization",
        "$.nested.email",
        "$.nested.phone",
        "$.message",
    }


def test_redaction_handles_lists_without_mutating_input() -> None:
    original = [{"note": "safe"}, {"password": "local-secret"}]

    cleaned, events = redact(original)

    assert cleaned == [{"note": "safe"}, {"password": "[REDACTED]"}]
    assert original[1]["password"] == "local-secret"
    assert events[0].path == "$[1].password"
