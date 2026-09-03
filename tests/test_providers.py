from __future__ import annotations

import pytest

from agent_tools.providers import ProviderConfig, resolve_provider


@pytest.mark.parametrize("provider", ["openai", "deepseek", "kimi", "minimax", "ollama"])
def test_provider_presets_have_openai_compatible_configuration(provider: str) -> None:
    config = resolve_provider(provider, env={})

    assert config.provider == provider
    assert config.base_url.startswith("http")
    assert config.model


def test_current_deepseek_and_kimi_default_models() -> None:
    assert resolve_provider("deepseek", env={}).model == "deepseek-v4-flash"
    assert resolve_provider("kimi", env={}).model == "kimi-k3"


def test_provider_environment_overrides_all_defaults() -> None:
    config = resolve_provider(
        "deepseek",
        env={
            "LLM_BASE_URL": "https://gateway.example/v1",
            "LLM_MODEL": "company-model",
            "LLM_API_KEY": "token",
        },
    )

    assert config == ProviderConfig(
        provider="deepseek",
        base_url="https://gateway.example/v1",
        model="company-model",
        api_key="token",
    )


@pytest.mark.parametrize(
    ("provider", "environment_name"),
    [
        ("openai", "OPENAI_API_KEY"),
        ("deepseek", "DEEPSEEK_API_KEY"),
        ("kimi", "MOONSHOT_API_KEY"),
        ("kimi", "KIMI_API_KEY"),
        ("minimax", "MINIMAX_API_KEY"),
    ],
)
def test_provider_uses_vendor_api_key(
    provider: str, environment_name: str
) -> None:
    config = resolve_provider(provider, env={environment_name: "vendor-token"})

    assert config.api_key == "vendor-token"


def test_generic_api_key_overrides_vendor_api_key() -> None:
    config = resolve_provider(
        "deepseek",
        env={"DEEPSEEK_API_KEY": "vendor-token", "LLM_API_KEY": "generic-token"},
    )

    assert config.api_key == "generic-token"


def test_custom_provider_requires_base_url_and_model() -> None:
    with pytest.raises(ValueError, match="LLM_BASE_URL"):
        resolve_provider("custom", env={})


def test_unknown_provider_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unsupported provider"):
        resolve_provider("mystery", env={})
