"""
Unit tests for new provider aliases in RigorousRAGEngine.
Verifies that CEREBRO_LLM_PROVIDER resolves correctly for all new providers.
"""

from unittest.mock import MagicMock, patch

import pytest


class TestEngineAliasResolution:
    """Test that _resolve_llm_provider_alias maps all new aliases correctly."""

    def test_alias_anthropic(self):
        from cerebro.core.rag.engine import RigorousRAGEngine

        assert RigorousRAGEngine._resolve_llm_provider_alias("anthropic") == "anthropic"

    def test_alias_claude(self):
        from cerebro.core.rag.engine import RigorousRAGEngine

        assert RigorousRAGEngine._resolve_llm_provider_alias("claude") == "anthropic"

    def test_alias_groq(self):
        from cerebro.core.rag.engine import RigorousRAGEngine

        assert RigorousRAGEngine._resolve_llm_provider_alias("groq") == "groq"

    def test_alias_gemini(self):
        from cerebro.core.rag.engine import RigorousRAGEngine

        assert RigorousRAGEngine._resolve_llm_provider_alias("gemini") == "gemini"

    def test_alias_google_gemini(self):
        from cerebro.core.rag.engine import RigorousRAGEngine

        assert RigorousRAGEngine._resolve_llm_provider_alias("google-gemini") == "gemini"

    def test_unknown_alias_raises_value_error(self):
        from cerebro.core.rag.engine import RigorousRAGEngine

        with pytest.raises(ValueError, match="Supported aliases"):
            RigorousRAGEngine._resolve_llm_provider_alias("ollama")

    def test_error_message_lists_supported_aliases(self):
        from cerebro.core.rag.engine import RigorousRAGEngine

        with pytest.raises(ValueError) as exc_info:
            RigorousRAGEngine._resolve_llm_provider_alias("unknown-provider")
        assert "anthropic" in str(exc_info.value)
        assert "groq" in str(exc_info.value)
        assert "gemini" in str(exc_info.value)


class TestEngineProviderFactory:
    """Test that _build_default_llm_provider instantiates the right class."""

    def test_anthropic_provider_instantiated(self, monkeypatch):
        monkeypatch.setenv("CEREBRO_LLM_PROVIDER", "anthropic")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")

        mock_provider = MagicMock()
        mock_cls = MagicMock(return_value=mock_provider)

        with patch("cerebro.providers.anthropic.AnthropicProvider", mock_cls):
            from cerebro.core.rag.engine import RigorousRAGEngine

            engine = RigorousRAGEngine.__new__(RigorousRAGEngine)
            engine.project_id = None
            engine.location = "global"
            engine.data_store_id = None
            engine.default_provider_name = "anthropic"
            result = engine._build_default_llm_provider()

        mock_cls.assert_called_once()
        assert result is mock_provider

    def test_groq_provider_instantiated(self, monkeypatch):
        monkeypatch.setenv("CEREBRO_LLM_PROVIDER", "groq")
        monkeypatch.setenv("GROQ_API_KEY", "gsk-test")

        mock_provider = MagicMock()
        mock_cls = MagicMock(return_value=mock_provider)

        with patch("cerebro.providers.groq.GroqProvider", mock_cls):
            from cerebro.core.rag.engine import RigorousRAGEngine

            engine = RigorousRAGEngine.__new__(RigorousRAGEngine)
            engine.project_id = None
            engine.location = "global"
            engine.data_store_id = None
            engine.default_provider_name = "groq"
            result = engine._build_default_llm_provider()

        mock_cls.assert_called_once()
        assert result is mock_provider

    def test_gemini_provider_instantiated(self, monkeypatch):
        monkeypatch.setenv("CEREBRO_LLM_PROVIDER", "gemini")
        monkeypatch.setenv("GEMINI_API_KEY", "AIza-test")

        mock_provider = MagicMock()
        mock_cls = MagicMock(return_value=mock_provider)

        with patch("cerebro.providers.gemini.GeminiProvider", mock_cls):
            from cerebro.core.rag.engine import RigorousRAGEngine

            engine = RigorousRAGEngine.__new__(RigorousRAGEngine)
            engine.project_id = None
            engine.location = "global"
            engine.data_store_id = None
            engine.default_provider_name = "gemini"
            result = engine._build_default_llm_provider()

        mock_cls.assert_called_once()
        assert result is mock_provider

    def test_claude_alias_routes_to_anthropic(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")

        mock_provider = MagicMock()
        mock_cls = MagicMock(return_value=mock_provider)

        with patch("cerebro.providers.anthropic.AnthropicProvider", mock_cls):
            from cerebro.core.rag.engine import RigorousRAGEngine

            engine = RigorousRAGEngine.__new__(RigorousRAGEngine)
            engine.project_id = None
            engine.location = "global"
            engine.data_store_id = None
            engine.default_provider_name = "claude"
            result = engine._build_default_llm_provider()

        mock_cls.assert_called_once()
        assert result is mock_provider
