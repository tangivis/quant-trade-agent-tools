from __future__ import annotations

import json

import httpx

from agent_tools.agent import OpenAICompatibleAgent
from agent_tools.providers import ProviderConfig
from agent_tools.tools import build_tool_registry


class FakeClient:
    def quote(self, symbol: str = "9984.T"):
        return {"price": 15500, "symbol": "9984.T"}

    def kline(self, interval: str, count: int, *, symbol: str = "9984.T"):
        return {"interval": interval, "count": count}

    def signals(self, symbol: str = "9984.T"):
        return {"signals": []}

    def news(self, count: int):
        return {"count": count}

    def sentiment(self):
        return {"score": 0}

    def trending(self, symbol: str = "9984.T"):
        return {"regime": "NarrowRange"}

    def backtest(self, strategy: str, days: int, **_kwargs):
        return {"strategy": strategy, "days": days}

    def benchmark(self, strategy: str, top: int, **_kwargs):
        return {"strategy": strategy, "top": top}

    def analyze(self, payload):
        return {"signal": "HOLD", "payload": payload}


def test_agent_executes_tool_call_then_returns_final_answer() -> None:
    payloads: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        payloads.append(payload)
        if len(payloads) == 1:
            return httpx.Response(
                200,
                json={
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": None,
                                "tool_calls": [
                                    {
                                        "id": "call_quote",
                                        "type": "function",
                                        "function": {
                                            "name": "quote",
                                            "arguments": "{}",
                                        },
                                    }
                                ],
                            }
                        }
                    ]
                },
            )
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "当前价格为 15500 日元。",
                        }
                    }
                ]
            },
        )

    agent = OpenAICompatibleAgent(
        config=ProviderConfig(
            provider="custom",
            base_url="https://llm.example/v1",
            model="test-model",
            api_key="token",
        ),
        tools=build_tool_registry(FakeClient()),
        transport=httpx.MockTransport(handler),
    )

    answer = agent.run("9984.T 现在多少钱？")

    assert answer == "当前价格为 15500 日元。"
    assert len(payloads) == 2
    assert payloads[0]["tools"][0]["function"]["name"] == "quote"
    tool_message = payloads[1]["messages"][-1]
    assert tool_message["role"] == "tool"
    assert json.loads(tool_message["content"])["price"] == 15500
    assert agent.last_tool_names == ["quote"]


def test_agent_includes_bounded_caller_history() -> None:
    captured: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(json.loads(request.content))
        return httpx.Response(
            200,
            json={"choices": [{"message": {"role": "assistant", "content": "完成"}}]},
        )

    agent = OpenAICompatibleAgent(
        config=ProviderConfig("custom", "https://llm.example/v1", "test", ""),
        tools=build_tool_registry(FakeClient()),
        transport=httpx.MockTransport(handler),
    )

    assert agent.run(
        "继续",
        history=[
            {"role": "user", "content": "先分析趋势"},
            {"role": "assistant", "content": "趋势偏强"},
        ],
    ) == "完成"
    assert captured[0]["messages"][1:] == [
        {"role": "user", "content": "先分析趋势"},
        {"role": "assistant", "content": "趋势偏强"},
        {"role": "user", "content": "继续"},
    ]


def test_agent_stops_after_iteration_limit() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": "again",
                                    "type": "function",
                                    "function": {"name": "quote", "arguments": "{}"},
                                }
                            ],
                        }
                    }
                ]
            },
        )

    agent = OpenAICompatibleAgent(
        config=ProviderConfig("custom", "https://llm.example/v1", "test", ""),
        tools=build_tool_registry(FakeClient()),
        max_iterations=1,
        transport=httpx.MockTransport(handler),
    )

    try:
        agent.run("loop")
    except RuntimeError as exc:
        assert "iteration limit" in str(exc)
    else:
        raise AssertionError("agent must stop infinite tool loops")
