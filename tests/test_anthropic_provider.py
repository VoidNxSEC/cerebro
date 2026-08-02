"""
Unit tests for AnthropicProvider.
All tests are fully mocked — no live API calls required.
"""

import sys
from unittest.mock import MagicMock, patch

import pytest


def _make_provider(api_key="sk-test", model="claude-sonnet-4-6"):
    from cerebro.providers.anthropic.llm import AnthropicProvider

    return AnthropicProvider(api_key=api_key, model=model)


class TestAnthropicProviderConstruction:
    def test_reads_env_vars(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "env-key")
        monkeypatch.setenv("ANTHROPIC_MODEL", "claude-opus-4-6")
        monkeypatch.setenv("ANTHROPIC_TIMEOUT", "60")
        from cerebro.providers.anthropic.llm import AnthropicProvider

        p = AnthropicProvider()
        assert p.api_key == "env-key"
        assert p.model == "claude-opus-4-6"
        assert p.timeout == 60.0

    def test_raises_without_api_key(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        from cerebro.providers.anthropic.llm import AnthropicProvider

        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
            AnthropicProvider()

    def test_constructor_args_override_env(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "env-key")
        monkeypatch.setenv("ANTHROPIC_MODEL", "claude-haiku-4-5")
        from cerebro.providers.anthropic.llm import AnthropicProvider

        p = AnthropicProvider(api_key="arg-key", model="claude-sonnet-4-6")
        assert p.api_key == "arg-key"
        assert p.model == "claude-sonnet-4-6"


class TestAnthropicEmbeddings:
    def test_embed_raises_not_implemented(self):
        p = _make_provider()
        with pytest.raises(NotImplementedError, match="embeddings API"):
            p.embed("hello")

    def test_embed_batch_raises_not_implemented(self):
        p = _make_provider()
        with pytest.raises(NotImplementedError, match="embeddings API"):
            p.embed_batch(["hello", "world"])


class TestAnthropicGenerate:
    def test_generate_returns_string(self):
        p = _make_provider()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="This is the answer.")]
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        p._client = mock_client

        result = p.generate("What is 2+2?")
        assert result == "This is the answer."
        mock_client.messages.create.assert_called_once()

    def test_generate_passes_kwargs(self):
        p = _make_provider()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="ok")]
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        p._client = mock_client

        p.generate("prompt", max_tokens=512, temperature=0.1)
        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert call_kwargs["max_tokens"] == 512
        assert call_kwargs["temperature"] == 0.1


class TestAnthropicGroundedGenerate:
    def test_returns_required_keys(self):
        p = _make_provider()
        p.generate = MagicMock(return_value="Based on [1], the answer is X.")

        result = p.grounded_generate("What is X?", context=["Context A", "Context B"], top_k=2)
        assert "answer" in result
        assert "citations" in result
        assert "snippets" in result
        assert "confidence" in result
        assert "cost_estimate" in result

    def test_returns_error_dict_on_exception(self):
        p = _make_provider()
        p.generate = MagicMock(side_effect=RuntimeError("API down"))

        result = p.grounded_generate("query", context=["ctx"])
        assert result["answer"].startswith("Error:")
        assert result["confidence"] == 0.0


class TestAnthropicHealthCheck:
    def test_returns_true_when_sdk_responds(self):
        p = _make_provider()
        mock_client = MagicMock()
        mock_client.models.list.return_value = MagicMock()
        p._client = mock_client

        assert p.health_check() is True

    def test_returns_false_on_exception(self):
        p = _make_provider()
        mock_client = MagicMock()
        mock_client.models.list.side_effect = Exception("connection refused")
        p._client = mock_client

        assert p.health_check() is False

    def test_import_error_gives_helpful_message(self):
        p = _make_provider()
        with patch.dict(sys.modules, {"anthropic": None}):
            p._client = None
            with pytest.raises(ImportError, match="poetry install --with anthropic"):
                p._get_client()
