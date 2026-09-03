"""OpenAI-compatible provider resolution for standalone agent mode."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class ProviderConfig:
    provider: str
    base_url: str
    model: str
    api_key: str


_PRESETS: dict[str, tuple[str, str]] = {
    "openai": ("https://api.openai.com/v1", "gpt-5"),
    "deepseek": ("https://api.deepseek.com/v1", "deepseek-v4-flash"),
    "kimi": ("https://api.moonshot.cn/v1", "kimi-k3"),
    "minimax": ("https://api.minimaxi.com/v1", "MiniMax-M3"),
    "ollama": ("http://127.0.0.1:11434/v1", "qwen3:8b"),
}

_PROVIDER_API_KEYS: dict[str, tuple[str, ...]] = {
    "openai": ("OPENAI_API_KEY",),
    "deepseek": ("DEEPSEEK_API_KEY",),
    "kimi": ("MOONSHOT_API_KEY", "KIMI_API_KEY"),
    "minimax": ("MINIMAX_API_KEY",),
}


def resolve_provider(
    provider: str | None = None,
    *,
    env: Mapping[str, str] | None = None,
) -> ProviderConfig:
    values = os.environ if env is None else env
    name = (provider or values.get("LLM_PROVIDER") or "openai").strip().lower()
    if name == "custom":
        base_url = values.get("LLM_BASE_URL", "").strip()
        model = values.get("LLM_MODEL", "").strip()
        if not base_url:
            raise ValueError("LLM_BASE_URL is required for custom provider")
        if not model:
            raise ValueError("LLM_MODEL is required for custom provider")
    else:
        try:
            default_base_url, default_model = _PRESETS[name]
        except KeyError as exc:
            raise ValueError(f"Unsupported provider: {name}") from exc
        base_url = values.get("LLM_BASE_URL", "").strip() or default_base_url
        model = values.get("LLM_MODEL", "").strip() or default_model
    provider_api_key = next(
        (
            values.get(environment_name, "").strip()
            for environment_name in _PROVIDER_API_KEYS.get(name, ())
            if values.get(environment_name, "").strip()
        ),
        "",
    )
    return ProviderConfig(
        provider=name,
        base_url=base_url.rstrip("/"),
        model=model,
        api_key=values.get("LLM_API_KEY", "").strip() or provider_api_key,
    )
