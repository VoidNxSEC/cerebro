"""
Factory helpers for LLM providers.
"""

from __future__ import annotations

from cerebro.interfaces.llm import LLMProvider
from cerebro.settings import get_settings

LLM_PROVIDER_ALIASES: dict[str, str] = {
    "llamacpp": "llamacpp",
    "llama.cpp": "llamacpp",
    "llama_cpp": "llamacpp",
    "local": "llamacpp",
    "anthropic": "anthropic",
    "claude": "anthropic",
    "azure": "azure",
    "azure_openai": "azure",
    "azure-openai": "azure",
    "gemini": "gemini",
    "google": "gemini",
    "groq": "groq",
    "openai_compatible": "openai_compatible",
    "openai-compatible": "openai_compatible",
    "openai": "openai_compatible",
    "gcp": "gcp",
    "vertex": "gcp",
    "vertexai": "gcp",
    "vertex_ai": "gcp",
}


def supported_llm_aliases() -> dict[str, str]:
    """Return a copy of supported LLM provider aliases."""

    return dict(LLM_PROVIDER_ALIASES)


def resolve_llm_provider_alias(provider_name: str) -> str:
    """Resolve an LLM provider alias to its canonical name."""

    normalized = provider_name.strip().lower()
    resolved = LLM_PROVIDER_ALIASES.get(normalized)
    if resolved:
        return resolved

    supported = ", ".join(
        f"{alias}->{canonical}"
        for alias, canonical in sorted(LLM_PROVIDER_ALIASES.items())
    )
    raise ValueError(
        f"Unsupported LLM provider value: {provider_name!r}. "
        f"Supported aliases: {supported}."
    )


def build_llm_provider(
    provider_name: str | None = None,
    *,
    # llamacpp
    base_url: str | None = None,
    model: str | None = None,
    # anthropic
    api_key: str | None = None,
    # azure
    chat_deployment: str | None = None,
    embed_deployment: str | None = None,
    # openai_compatible
    openai_api_base: str | None = None,
    openai_model: str | None = None,
) -> LLMProvider:
    """Build the configured LLM provider."""

    settings = get_settings()
    canonical_name = resolve_llm_provider_alias(
        provider_name or settings.llm_provider,
    )

    if canonical_name == "llamacpp":
        from cerebro.providers.llamacpp.llm import LlamaCppProvider

        kwargs: dict = {}
        if base_url:
            kwargs["base_url"] = base_url
        if model:
            kwargs["model"] = model
        return LlamaCppProvider(**kwargs)

    if canonical_name == "anthropic":
        from cerebro.providers.anthropic.llm import AnthropicProvider

        kwargs = {}
        if api_key:
            kwargs["api_key"] = api_key
        if model:
            kwargs["model"] = model
        return AnthropicProvider(**kwargs)

    if canonical_name == "azure":
        from cerebro.providers.azure.azure_provider import AzureOpenAIProvider

        return AzureOpenAIProvider(
            chat_deployment=chat_deployment,
            embed_deployment=embed_deployment,
        )

    if canonical_name == "gemini":
        from cerebro.providers.gemini.llm import GeminiProvider

        kwargs = {}
        if api_key:
            kwargs["api_key"] = api_key
        if model:
            kwargs["model"] = model
        return GeminiProvider(**kwargs)

    if canonical_name == "groq":
        from cerebro.providers.groq.llm import GroqProvider

        kwargs = {}
        if api_key:
            kwargs["api_key"] = api_key
        if model:
            kwargs["model"] = model
        return GroqProvider(**kwargs)

    if canonical_name == "openai_compatible":
        from cerebro.providers.openai_compatible.llm import OpenAICompatibleProvider

        kwargs = {}
        if openai_api_base or base_url:
            kwargs["base_url"] = openai_api_base or base_url
        if api_key:
            kwargs["api_key"] = api_key
        if openai_model or model:
            kwargs["model"] = openai_model or model
        return OpenAICompatibleProvider(**kwargs)

    if canonical_name == "gcp":
        from cerebro.providers.gcp.vertex_ai_llm import VertexAILLMProvider

        return VertexAILLMProvider()

    raise ValueError(
        f"LLM provider is not implemented yet: {canonical_name!r}."
    )
