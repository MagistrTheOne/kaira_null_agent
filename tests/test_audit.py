from services.audit import redact_secrets


def test_redacts_common_secret_shapes() -> None:
    payload = {
        "firecrawl": "fc-secret-value",
        "openai": "sk-secret-value",
        "text": "api_key=super-secret",
    }

    redacted = redact_secrets(payload)

    assert redacted["firecrawl"] == "[REDACTED]"
    assert redacted["openai"] == "[REDACTED]"
    assert "[REDACTED]" in redacted["text"]
