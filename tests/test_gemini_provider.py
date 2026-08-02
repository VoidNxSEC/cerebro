"""
Unit tests for GeminiProvider.
All tests are fully mocked — no live API calls required.
google-genai is an optional dependency, so we stub the entire module in sys.modules.
"""

import sys
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Stub google.genai so imports succeed without the optional package installed
# ---------------------------------------------------------------------------
_mock_types = MagicMock()
_mock_genai_module = MagicMock()
_mock_genai_module.Client = MagicMock
_google_stub = MagicMock()
_google_stub.genai = _mock_genai_module

_GOOGLE_STUBS = {
    "google": _google_stub,
    "google.genai": _mock_genai_module,
    "google.genai.types": _mock_types,
}

# Ensure the attribute and sys.modules entry point to the same object
_mock_genai_module.types = _mock_types

# Inject stubs before any test imports the provider
for _mod, _stub in _GOOGLE_STUBS.items():
    sys.modules.setdefault(_mod, _stub)


def _make_provider(api_key="AIza-test", model="gemini-1.5-flash"):
    from cerebro.providers.gemini.llm import GeminiProvider

    return GeminiProvider(api_key=api_key, model=model)


def _mock_embedding(values: list[float]) -> MagicMock:
    emb = MagicMock()
    emb.values = values
    resp = MagicMock()
    resp.embeddings = [emb]
    return resp


class TestGeminiProviderConstruction:
    def test_reads_env_vars(self, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "env-key")
        monkeypatch.setenv("GEMINI_MODEL", "gemini-1.5-pro")
        monkeypatch.setenv("GEMINI_EMBEDDING_MODEL", "models/embedding-001")
        monkeypatch.setenv("GEMINI_TIMEOUT", "60")
        from cerebro.providers.gemini.llm import GeminiProvider

        p = GeminiProvider()
        assert p.api_key == "env-key"
        assert p.model == "gemini-1.5-pro"
        assert p.embedding_model == "models/embedding-001"
        assert p.timeout == 60.0

    def test_raises_without_api_key(self, monkeypatch):
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        from cerebro.providers.gemini.llm import GeminiProvider

        with pytest.raises(ValueError, match="GEMINI_API_KEY"):
            GeminiProvider()


class TestGeminiEmbeddings:
    def test_embed_returns_vector(self):
        p = _make_provider()
        mock_client = MagicMock()
        mock_client.models.embed_content.return_value = _mock_embedding([0.1, 0.2, 0.3])
        p._client = mock_client

        result = p.embed("hello world")
        assert result == [0.1, 0.2, 0.3]

    def test_embed_batch_calls_per_text(self):
        p = _make_provider()
        mock_client = MagicMock()
        mock_client.models.embed_content.side_effect = [
            _mock_embedding([0.1, 0.2]),
            _mock_embedding([0.3, 0.4]),
        ]
        p._client = mock_client

        result = p.embed_batch(["text a", "text b"])
        assert len(result) == 2
        assert result[0] == [0.1, 0.2]
        assert result[1] == [0.3, 0.4]
        assert mock_client.models.embed_content.call_count == 2

    def test_embed_batch_respects_batch_size(self):
        p = _make_provider()
        mock_client = MagicMock()
        mock_client.models.embed_content.return_value = _mock_embedding([0.0])
        p._client = mock_client

        p.embed_batch(["a", "b", "c"], batch_size=2)
        assert mock_client.models.embed_content.call_count == 3


class TestGeminiGenerate:
    def test_generate_returns_text(self):
        p = _make_provider()
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Gemini answer."
        mock_client.models.generate_content.return_value = mock_response
        p._client = mock_client

        result = p.generate("What is AI?")
        assert result == "Gemini answer."

    def test_generate_passes_generation_config(self):
        p = _make_provider()
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "ok"
        mock_client.models.generate_content.return_value = mock_response
        p._client = mock_client

        # Reset call history on the mocked types so we can inspect this call only
        _mock_types.GenerateContentConfig.reset_mock()
        p.generate("prompt", max_tokens=512, temperature=0.2)
        config_call = _mock_types.GenerateContentConfig.call_args
        assert config_call.kwargs["max_output_tokens"] == 512
        assert config_call.kwargs["temperature"] == 0.2


class TestGeminiGroundedGenerate:
    def test_returns_required_keys(self):
        p = _make_provider()
        p.generate = MagicMock(return_value="Grounded answer from [1].")

        result = p.grounded_generate("Query?", context=["Doc A", "Doc B"], top_k=2)
        assert "answer" in result
        assert "citations" in result
        assert "snippets" in result
        assert "confidence" in result
        assert "cost_estimate" in result

    def test_returns_error_dict_on_exception(self):
        p = _make_provider()
        p.generate = MagicMock(side_effect=RuntimeError("quota exceeded"))

        result = p.grounded_generate("query", context=["ctx"])
        assert result["answer"].startswith("Error:")
        assert result["confidence"] == 0.0


class TestGeminiHealthCheck:
    def test_returns_true_when_api_responds(self):
        p = _make_provider()
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = MagicMock(text="pong")
        p._client = mock_client

        assert p.health_check() is True

    def test_returns_false_on_exception(self):
        p = _make_provider()
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("API error")
        p._client = mock_client

        assert p.health_check() is False

    def test_import_error_gives_helpful_message(self):
        p = _make_provider()
        p._client = None
        with patch.dict(sys.modules, {"google": None, "google.genai": None, "google.genai.types": None}):
            with pytest.raises((ImportError, Exception)):
                p._get_client()
