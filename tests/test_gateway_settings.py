from __future__ import annotations

import pytest

from agent_tools.gateway.app import _default_analysis_provider
from agent_tools.gateway.config import GatewaySettings
from agent_tools.gateway.services import LegacyAnalysisProvider, NativeAnalysisProvider


def test_gateway_settings_default_to_native(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TRADE_AGENT_ORCHESTRATION_MODE", raising=False)

    assert GatewaySettings().orchestration_mode == "native"
    assert GatewaySettings.from_env().orchestration_mode == "native"
    assert isinstance(_default_analysis_provider("native"), NativeAnalysisProvider)


def test_legacy_mode_is_an_explicit_rollback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRADE_AGENT_ORCHESTRATION_MODE", "legacy")

    settings = GatewaySettings.from_env()

    assert settings.orchestration_mode == "legacy"
    assert isinstance(_default_analysis_provider("legacy"), LegacyAnalysisProvider)


def test_unimplemented_shadow_mode_is_rejected() -> None:
    with pytest.raises(ValueError, match="not implemented"):
        GatewaySettings(orchestration_mode="shadow")
