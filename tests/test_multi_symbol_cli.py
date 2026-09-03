from __future__ import annotations

from typing import Any

from click.testing import CliRunner

from agent_tools import cli


def test_cli_maps_symbol_and_structured_backtest_options(monkeypatch) -> None:
    calls: list[tuple[str, dict[str, Any]]] = []

    def fake_call(name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        calls.append((name, arguments or {}))
        return {"ok": True}

    monkeypatch.setattr(cli, "_call_tool", fake_call)
    result = CliRunner().invoke(
        cli.main,
        [
            "backtest",
            "--symbol",
            "6981.T",
            "--strategy",
            "rsi",
            "--interval",
            "15m",
            "--days",
            "90",
            "--initial-cash",
            "2500000",
            "--risk-params",
            '{"max_position_pct":0.2}',
        ],
    )

    assert result.exit_code == 0, result.output
    assert calls == [
        (
            "backtest",
            {
                "symbol": "6981.T",
                "strategy": "rsi",
                "interval": "15m",
                "days": 90,
                "initial_cash": 2_500_000.0,
                "risk_params": {"max_position_pct": 0.2},
            },
        )
    ]


def test_cli_rejects_unknown_symbol_without_dispatch(monkeypatch) -> None:
    calls: list[tuple[str, dict[str, Any]]] = []
    monkeypatch.setattr(
        cli,
        "_call_tool",
        lambda name, arguments=None: calls.append((name, arguments or {})),
    )

    result = CliRunner().invoke(cli.main, ["quote", "--symbol", "UNKNOWN"])

    assert result.exit_code != 0
    assert calls == []


def test_cli_rejects_non_object_risk_params(monkeypatch) -> None:
    monkeypatch.setattr(cli, "_call_tool", lambda *_args, **_kwargs: {"ok": True})

    result = CliRunner().invoke(
        cli.main,
        ["benchmark", "--strategy", "rsi", "--risk-params", "[]"],
    )

    assert result.exit_code != 0
    assert "JSON object" in result.output
