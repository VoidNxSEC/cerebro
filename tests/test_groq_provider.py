"""
Unit tests for GroqProvider.
All tests are fully mocked — no live API calls required.
"""

import sys
from unittest.mock import MagicMock, patch

import pytest


def _make_provider(api_key="gsk-test", model="llama-3.3-70b-versatile"):
    from cerebro.providers.groq.llm import GroqProvider

    return GroqProvider(api_key=api_key, model=model)


class TestGroqProviderConstruction:
    def test_reads_env_vars(self, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "env-key")
        monkeypatch.setenv("GROQ_MODEL", "mixtral-8x7b-32768")
        monkeypatch.setenv("GROQ_TIMEOUT", "30")
        from cerebro.providers.groq.llm import GroqProvider

        p = GroqProvider()
        assert p.api_key == "env-key"
        assert p.model == "mixtral-8x7b-32768"
        assert p.timeout == 30.0

    def test_raises_without_api_key(self, monkeypatch):
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        from cerebro.providers.groq.llm import GroqProvider

        with pytest.raises(ValueError, match="GROQ_API_KEY"):
            GroqProvider()

    def test_constructor_args_override_env(self, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "env-key")
        from cerebro.providers.groq.llm import GroqProvider

        p = GroqProvider(api_key="arg-key", model="gemma2-9b-it")
        assert p.api_key == "arg-key"
        assert p.model == "gemma2-9b-it"


class TestGroqEmbeddings:
    def test_embed_raises_not_implemented(self):
        p = _make_provider()
        with pytest.raises(NotImplementedError, match="embeddings API"):
            p.embed("hello")

    def test_embed_batch_raises_not_implemented(self):
        p = _make_provider()
        with pytest.raises(NotImplementedError, match="embeddings API"):
            p.embed_batch(["hello", "world"])


class TestGroqGenerate:
    def test_generate_returns_string(self):
        p = _make_provider()
        mock_choice = MagicMock()
        mock_choice.message.content = "Fast answer."
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        p._client = mock_client

        result = p.generate("What is 2+2?")
        assert result == "Fast answer."

    def test_generate_passes_kwargs(self):
        p = _make_provider()
        mock_choice = MagicMock()
        mock_choice.message.content = "ok"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        p._client = mock_client

        p.generate("prompt", max_tokens=256, temperature=0.0)
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["max_tokens"] == 256
        assert call_kwargs["temperature"] == 0.0


class TestGroqGroundedGenerate:
    def test_returns_required_keys(self):
        p = _make_provider()
        p.generate = MagicMock(return_value="The answer is in [1].")

        result = p.grounded_generate("Query?", context=["Doc A", "Doc B"], top_k=2)
        assert "answer" in result
        assert "citations" in result
        assert "snippets" in result
        assert "confidence" in result
        assert "cost_estimate" in result

    def test_returns_error_dict_on_exception(self):
        p = _make_provider()
        p.generate = MagicMock(side_effect=RuntimeError("rate limit"))

        result = p.grounded_generate("query", context=["ctx"])
        assert result["answer"].startswith("Error:")
        assert result["confidence"] == 0.0


class TestGroqHealthCheck:
    def test_returns_true_when_sdk_responds(self):
        p = _make_provider()
        mock_client = MagicMock()
        mock_client.models.list.return_value = MagicMock()
        p._client = mock_client

        assert p.health_check() is True

    def test_returns_false_on_exception(self):
        p = _make_provider()
        mock_client = MagicMock()
        mock_client.models.list.side_effect = Exception("timeout")
        p._client = mock_client

        assert p.health_check() is False

    def test_import_error_gives_helpful_message(self):
        p = _make_provider()
        with patch.dict(sys.modules, {"groq": None}):
            p._client = None
            with pytest.raises(ImportError, match="poetry install --with groq"):
                p._get_client()
