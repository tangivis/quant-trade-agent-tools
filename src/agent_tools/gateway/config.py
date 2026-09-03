"""Environment-backed Gateway configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal


OrchestrationMode = Literal["legacy", "native", "shadow"]


@dataclass(frozen=True)
class GatewaySettings:
    api_token: str = ""
    orchestration_mode: OrchestrationMode = "native"
    max_history_messages: int = 20

    def __post_init__(self) -> None:
        if self.orchestration_mode not in {"native", "legacy"}:
            raise ValueError(
                f"Orchestration mode is not implemented: {self.orchestration_mode}"
            )
        if self.max_history_messages < 0:
            raise ValueError("max_history_messages must not be negative")

    @classmethod
    def from_env(cls) -> GatewaySettings:
        mode = os.getenv("TRADE_AGENT_ORCHESTRATION_MODE", "native").strip().lower()
        if mode not in {"legacy", "native", "shadow"}:
            raise ValueError(f"Unsupported orchestration mode: {mode}")
        max_history = int(os.getenv("TRADE_AGENT_MAX_HISTORY", "20"))
        return cls(
            api_token=os.getenv("TRADE_AGENT_API_TOKEN", "").strip(),
            orchestration_mode=mode,  # type: ignore[arg-type]
            max_history_messages=max_history,
        )
