import os

from .gemini import GeminiProvider
from .provider import LlmProvider


def get_provider() -> LlmProvider:
    """Builds the configured LlmProvider from environment variables (§7, §9).

    Swapping providers for the comparative experiment (PI-3) is just
    changing LLM_PROVIDER — the pipeline stages never import a provider
    class directly.
    """
    provider_name = os.environ.get("LLM_PROVIDER", "").lower()
    api_key = os.environ.get("LLM_API_KEY", "")
    model = os.environ.get("LLM_MODEL", "")

    if not provider_name:
        raise RuntimeError("LLM_PROVIDER is not set")
    if not api_key:
        raise RuntimeError("LLM_API_KEY is not set")
    if not model:
        raise RuntimeError("LLM_MODEL is not set")

    if provider_name == "gemini":
        return GeminiProvider(api_key=api_key, model=model)

    raise RuntimeError(f"Unknown LLM_PROVIDER: {provider_name!r}")
