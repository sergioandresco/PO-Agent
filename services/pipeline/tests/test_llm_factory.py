import pytest

from services.pipeline.llm import GeminiProvider, get_provider


def test_get_provider_builds_gemini(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("LLM_API_KEY", "fake-key")
    monkeypatch.setenv("LLM_MODEL", "gemini-3.1-flash-lite")

    provider = get_provider()

    assert isinstance(provider, GeminiProvider)
    assert provider.name == "gemini"


@pytest.mark.parametrize("missing_var", ["LLM_PROVIDER", "LLM_API_KEY", "LLM_MODEL"])
def test_get_provider_requires_every_env_var(
    monkeypatch: pytest.MonkeyPatch, missing_var: str
) -> None:
    env = {
        "LLM_PROVIDER": "gemini",
        "LLM_API_KEY": "fake-key",
        "LLM_MODEL": "gemini-3.1-flash-lite",
    }
    del env[missing_var]
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    monkeypatch.delenv(missing_var, raising=False)

    with pytest.raises(RuntimeError, match=missing_var):
        get_provider()


def test_get_provider_rejects_unknown_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "not-a-real-provider")
    monkeypatch.setenv("LLM_API_KEY", "fake-key")
    monkeypatch.setenv("LLM_MODEL", "some-model")

    with pytest.raises(RuntimeError, match="Unknown LLM_PROVIDER"):
        get_provider()
