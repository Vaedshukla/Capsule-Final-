import pytest
from app.ingestion.sanitizer import sanitizer

def test_sanitizer_removes_api_keys():
    # OpenAI
    res = sanitizer.sanitize("Here is my key: sk-proj-1234567890abcdefghij1234567890")
    assert "sk-proj" not in res.content
    assert "[REDACTED:openai_key]" in res.content
    assert res.redaction_count == 1
    assert "openai_api_key" in res.patterns_matched

    # Anthropic
    res = sanitizer.sanitize("Use sk-ant-api03-abcdefg1234567890abcdefg")
    assert "sk-ant" not in res.content
    assert "[REDACTED:anthropic_key]" in res.content

def test_sanitizer_removes_jwt():
    jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI.eyJzdWIiOiIxMjM0NTY3ODkwIiw.SflKxwRJSMeKKF"
    res = sanitizer.sanitize(f"Token is {jwt}")
    assert jwt not in res.content
    assert "[REDACTED:jwt]" in res.content

def test_sanitizer_removes_db_connection_strings():
    conn = "postgres://user:pass@localhost:5432/db"
    res = sanitizer.sanitize(f"Connect using {conn}")
    assert conn not in res.content
    assert "[REDACTED:connection_string]" in res.content

def test_sanitizer_leaves_normal_text_alone():
    text = "Just a normal message about code architecture. We should use FastAPI."
    res = sanitizer.sanitize(text)
    assert res.content == text
    assert res.redaction_count == 0
