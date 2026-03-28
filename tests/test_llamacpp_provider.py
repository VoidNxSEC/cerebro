"""
Tests for LlamaCppProvider.

Live tests (require server at localhost:8081) are skipped when the server
is offline so CI doesn't break.
"""

import pytest

from cerebro.providers.llamacpp import LlamaCppProvider

SERVER_URL = "http://localhost:8081"


def _server_online() -> bool:
    provider = LlamaCppProvider(base_url=SERVER_URL)
    return provider.health_check()


# ── Unit tests (no server needed) ─────────────────────────────────────────────

def test_default_model():
    p = LlamaCppProvider()
    assert p.model == "current-model"


def test_custom_url_and_model():
    p = LlamaCppProvider(base_url="http://localhost:9999", model="mymodel")
    assert p.base_url == "http://localhost:9999"
    assert p.model == "mymodel"


def test_trailing_slash_stripped():
    p = LlamaCppProvider(base_url="http://localhost:8081/")
    assert p.base_url == "http://localhost:8081"


# ── Live tests (require running server) ───────────────────────────────────────

@pytest.mark.skipif(not _server_online(), reason="llama.cpp server not running")
def test_health_check():
    p = LlamaCppProvider(base_url=SERVER_URL)
    assert p.health_check() is True


@pytest.mark.skipif(not _server_online(), reason="llama.cpp server not running")
def test_generate_returns_string():
    p = LlamaCppProvider(base_url=SERVER_URL)
    result = p.generate("Reply with exactly: OK", max_tokens=5)
    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.skipif(not _server_online(), reason="llama.cpp server not running")
def test_grounded_generate_structure():
    p = LlamaCppProvider(base_url=SERVER_URL)
    result = p.grounded_generate(
        query="What is the project?",
        context=["Cerebro is an enterprise knowledge platform."],
        top_k=1,
        max_tokens=30,
    )
    assert "answer" in result
    assert "citations" in result
    assert isinstance(result["answer"], str)


@pytest.mark.skipif(not _server_online(), reason="llama.cpp server not running")
def test_embed_raises_when_not_supported():
    """Embeddings require --embeddings flag — expect clear RuntimeError."""
    p = LlamaCppProvider(base_url=SERVER_URL)
    with pytest.raises(RuntimeError, match="--embeddings"):
        p.embed("test")
