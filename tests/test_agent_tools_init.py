"""TDD: agent_tools Python 核心包装层 (src-layout compatible).

Tests verify the agent_tools package works when imported as `agent_tools`
(matching the existing backend_llm src-layout convention) and when invoked
via `python -m agent_tools`.

This file is the TDD RED phase baseline. Tests must pass before the change
is considered complete.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

# Tests run from backend_llm/ where src/ is on sys.path via conftest or pytest.ini.
# The existing test_agents.py uses the same pattern (e.g. `from src.agents.graph`).


# ============================================================
# 1. Top-level import (src-layout)
# ============================================================


def test_agent_tools_importable():
    """agent_tools package 必须可以 import."""
    import agent_tools
    assert agent_tools is not None


def test_agent_tools_has_version():
    """agent_tools 必须暴露 __version__."""
    import agent_tools
    assert hasattr(agent_tools, "__version__")
    assert isinstance(agent_tools.__version__, str)
    assert agent_tools.__version__  # non-empty


# ============================================================
# 2. CLI entry point
# ============================================================


def test_agent_tools_cli_help_exits_zero():
    """`python -m agent_tools --help` 必须 exit 0."""
    # Run from backend_llm/ so src/ is on path
    result = subprocess.run(
        ["uv", "run", "python", "-m", "agent_tools", "--help"],
        cwd=str(Path(__file__).parent.parent),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"


def test_agent_tools_cli_lists_canonical_subcommands():
    """`python -m agent_tools --help` 必须列出 canonical subcommand."""
    expected = {"quote", "kline", "signals", "news", "sentiment",
                "trending", "backtest", "benchmark", "analyze",
                "conversation_create", "conversation_context",
                "conversation_append"}
    result = subprocess.run(
        ["uv", "run", "python", "-m", "agent_tools", "--help"],
        cwd=str(Path(__file__).parent.parent),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0
    for sub in expected:
        assert sub in result.stdout, f"missing subcommand: {sub}"
    assert "gateway" in result.stdout


def test_importing_cli_does_not_import_fastapi() -> None:
    result = subprocess.run(
        [
            "uv",
            "run",
            "python",
            "-c",
            "import sys; import agent_tools.cli; assert 'fastapi' not in sys.modules",
        ],
        cwd=str(Path(__file__).parent.parent),
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr


def test_agent_tools_analyze_subcommand_exposes_native_inputs_only():
    """The analyze CLI exposes only symbol and an optional question."""
    result = subprocess.run(
        ["uv", "run", "python", "-m", "agent_tools", "analyze", "--help"],
        cwd=str(Path(__file__).parent.parent),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "--symbol" in result.stdout
    assert "--question" in result.stdout
    assert "--offline" not in result.stdout
    assert "--price" not in result.stdout


# ============================================================
# 3. analyze maps only native Gateway inputs
# ============================================================


def test_agent_tools_analyze_maps_symbol_and_question(monkeypatch):
    from click.testing import CliRunner

    from agent_tools import cli

    captured = []
    monkeypatch.setattr(
        cli,
        "run_analyze",
        lambda **kwargs: captured.append(kwargs) or {"decision": {"action": "HOLD"}},
    )
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "analyze",
            "--symbol",
            "6981.T",
            "--question",
            "说明风险",
        ],
    )
    assert result.exit_code == 0, f"output: {result.output}\nexc: {result.exception}"
    assert captured == [{"symbol": "6981.T", "question": "说明风险"}]



def test_agent_tools_mcp_server_module_exists():
    """agent_tools.mcp_server 模块必须存在."""
    import agent_tools.mcp_server  # noqa: F401


def test_agent_tools_mcp_server_exposes_canonical_tool_names():
    """MCP server must expose market and conversation tools."""
    from agent_tools.mcp_server import TOOL_NAMES

    assert len(TOOL_NAMES) == 12
    expected = {"quote", "kline", "signals", "news", "sentiment",
                "trending", "backtest", "benchmark", "analyze",
                "conversation_create", "conversation_context",
                "conversation_append"}
    assert set(TOOL_NAMES) == expected


# ============================================================
# 5. 行情 canonical tool name 兼容性
# ============================================================


@pytest.mark.parametrize("tool_name", [
    "quote", "kline", "signals", "news", "sentiment",
    "trending", "backtest", "benchmark", "analyze",
])
def test_agent_tools_exposes_tool_name(tool_name):
    """行情 tool name 必须作为 CLI subcommand 存在."""
    result = subprocess.run(
        ["uv", "run", "python", "-m", "agent_tools", tool_name, "--help"],
        cwd=str(Path(__file__).parent.parent),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, f"{tool_name} --help failed: {result.stderr}"
