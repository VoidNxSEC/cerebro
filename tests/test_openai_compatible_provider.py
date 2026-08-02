"""
Tests for OpenAICompatibleProvider.
"""

import json
from unittest.mock import patch

from cerebro.providers.openai_compatible import OpenAICompatibleProvider


class _FakeResponse:
    def __init__(self, payload: dict, status: int = 200):
        self._payload = payload
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(self._payload).encode("utf-8")


def test_default_constructor_uses_env_defaults():
    provider = OpenAICompatibleProvider()

    assert provider.base_url == "http://localhost:8000"
    assert provider.model == "current-model"
    assert provider.api_key is None
    assert provider.timeout == 120.0


def test_constructor_normalizes_url_and_reads_env(monkeypatch):
    monkeypatch.setenv("OPENAI_COMPATIBLE_URL", "http://localhost:9000/")
    monkeypatch.setenv("OPENAI_COMPATIBLE_MODEL", "test-model")
    monkeypatch.setenv("OPENAI_COMPATIBLE_API_KEY", "secret")
    monkeypatch.setenv("OPENAI_COMPATIBLE_TIMEOUT", "15")

    provider = OpenAICompatibleProvider()

    assert provider.base_url == "http://localhost:9000"
    assert provider.model == "test-model"
    assert provider.api_key == "secret"
    assert provider.timeout == 15.0


def test_embed_returns_first_vector():
    provider = OpenAICompatibleProvider(base_url="http://example.test", model="m")

    payload = {
        "data": [
            {"index": 1, "embedding": [0.2, 0.3]},
            {"index": 0, "embedding": [0.1, 0.2]},
        ]
    }

    with patch("cerebro.providers.openai_compatible.llm.urllib.request.urlopen", return_value=_FakeResponse(payload)) as mock_urlopen:
        result = provider.embed("hello")

    assert result == [0.1, 0.2]
    assert mock_urlopen.call_count == 1


def test_generate_posts_chat_completion():
    provider = OpenAICompatibleProvider(base_url="http://example.test", model="m")

    payload = {"choices": [{"message": {"content": "OK"}}]}

    with patch("cerebro.providers.openai_compatible.llm.urllib.request.urlopen", return_value=_FakeResponse(payload)) as mock_urlopen:
        result = provider.generate("Say OK", temperature=0.1, max_tokens=16)

    assert result == "OK"
    assert mock_urlopen.call_count == 1


def test_grounded_generate_builds_context_and_returns_structure():
    provider = OpenAICompatibleProvider()

    with patch.object(provider, "generate", return_value="Grounded answer") as mock_generate:
        result = provider.grounded_generate(
            query="What is Cerebro?",
            context=["Cerebro is a knowledge platform.", "It supports providers."],
            top_k=1,
            temperature=0.2,
        )

    assert result["answer"] == "Grounded answer"
    assert result["citations"] == ["[1]"]
    assert result["snippets"] == ["Cerebro is a knowledge platform."]
    assert result["confidence"] == 0.9
    assert result["cost_estimate"] == 0.0
    mock_generate.assert_called_once()


def test_health_check_succeeds_on_health_endpoint():
    provider = OpenAICompatibleProvider(base_url="http://example.test")

    with patch("cerebro.providers.openai_compatible.llm.urllib.request.urlopen", return_value=_FakeResponse({}, status=200)) as mock_urlopen:
        assert provider.health_check() is True

    assert mock_urlopen.call_count >= 1
