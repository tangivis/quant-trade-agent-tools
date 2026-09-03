from __future__ import annotations

import json

import httpx
import pytest

from agent_tools.client import QuantTradeClient


def test_client_uses_separate_api_and_gateway_bases_and_tokens() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"url": str(request.url)})

    client = QuantTradeClient(
        api_base_url="http://quant.test:5188",
        agent_base_url="http://gateway.test:8010",
        api_token="product-token",
        agent_token="gateway-token",
        transport=httpx.MockTransport(handler),
    )

    client.quote()
    client.analyze(symbol="6981.T", question="关注风险")

    assert str(requests[0].url) == "http://quant.test:5188/api/quote?symbol=9984.T"
    assert requests[0].headers["authorization"] == "Bearer product-token"
    assert str(requests[1].url) == "http://gateway.test:8010/v1/analyze"
    assert requests[1].headers["authorization"] == "Bearer gateway-token"
    assert json.loads(requests[1].content) == {
        "symbol": "6981.T",
        "question": "关注风险",
        "mode": "standard",
    }


def test_client_sends_bearer_token_when_configured() -> None:
    seen_auth: list[str | None] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_auth.append(request.headers.get("authorization"))
        return httpx.Response(200, json={"ok": True})

    client = QuantTradeClient(
        api_token="secret-token",
        transport=httpx.MockTransport(handler),
    )

    client.signals()

    assert seen_auth == ["Bearer secret-token"]


def test_client_rejects_non_object_json() -> None:
    client = QuantTradeClient(
        transport=httpx.MockTransport(
            lambda _request: httpx.Response(200, json=["unexpected"])
        )
    )

    try:
        client.quote()
    except ValueError as exc:
        assert "JSON object" in str(exc)
    else:
        raise AssertionError("non-object backend response must fail")


def test_news_wraps_upstream_array_in_object() -> None:
    seen_url: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_url.append(str(request.url))
        return httpx.Response(200, json=[{"title": "SoftBank"}])

    client = QuantTradeClient(transport=httpx.MockTransport(handler))

    assert client.news(3) == {"articles": [{"title": "SoftBank"}]}
    assert seen_url == ["http://127.0.0.1:5188/api/intel/news?count=3"]


def test_kline_returns_only_newest_requested_candles() -> None:
    seen_url: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_url.append(str(request.url))
        return httpx.Response(
            200,
            json={"symbol": "9984.T", "candles": [{"id": 1}, {"id": 2}, {"id": 3}]},
        )

    client = QuantTradeClient(transport=httpx.MockTransport(handler))

    result = client.kline("5m", 2)

    assert result["candles"] == [{"id": 2}, {"id": 3}]
    assert seen_url == [
        "http://127.0.0.1:5188/api/kline?symbol=9984.T&interval=5m"
    ]


def test_backtest_maps_strategy_to_historical_backend_contract() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"metrics": {}})

    client = QuantTradeClient(transport=httpx.MockTransport(handler))

    client.backtest("vwap", 90)

    assert requests[0].url.path == "/api/backtest/historical"
    assert json.loads(requests[0].content) == {
        "symbol": "9984.T",
        "strategy": "vwap",
        "interval": "5m",
        "days": 90,
        "risk_params": {},
    }


def test_unknown_backtest_strategy_is_rejected() -> None:
    client = QuantTradeClient(transport=httpx.MockTransport(lambda _request: None))

    with pytest.raises(ValueError, match="Unsupported strategy"):
        client.backtest("mystery", 60)


def test_benchmark_uses_supported_request_and_filters_results() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "results": [
                    {"strategy_id": "rsi", "sharpe_ratio": 2.0},
                    {"strategy_id": "ma_cross", "sharpe_ratio": 1.5},
                    {"strategy_id": "rsi", "sharpe_ratio": 1.0},
                ],
                "best_overall": {"strategy_id": "rsi", "sharpe_ratio": 2.0},
            },
        )

    client = QuantTradeClient(transport=httpx.MockTransport(handler))

    result = client.benchmark("rsi", 1)

    assert json.loads(requests[0].content) == {
        "symbol": "9984.T",
        "interval": "5m",
        "risk_params": {},
        "use_history": True,
    }
    assert requests[0].extensions["timeout"]["read"] == 1800.0
    assert result["results"] == [{"strategy_id": "rsi", "sharpe_ratio": 2.0}]
    assert result["best_overall"] == {"strategy_id": "rsi", "sharpe_ratio": 2.0}


def test_benchmark_rejects_strategy_not_scanned_upstream() -> None:
    client = QuantTradeClient(transport=httpx.MockTransport(lambda _request: None))

    with pytest.raises(ValueError, match="Unsupported benchmark strategy"):
        client.benchmark("vwap", 5)


def test_conversation_client_uses_product_api_and_bearer() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"id": "thread-1", "messages": []})

    client = QuantTradeClient(
        api_base_url="http://quant.test:5188",
        api_token="user-token",
        transport=httpx.MockTransport(handler),
    )

    client.conversation_context("thread-1")
    client.conversation_append("thread-1", role="user", content="继续分析")

    assert requests[0].url.path == "/api/conversations/thread-1/context"
    assert requests[1].url.path == "/api/conversations/thread-1/messages"
    assert requests[0].headers["authorization"] == "Bearer user-token"
