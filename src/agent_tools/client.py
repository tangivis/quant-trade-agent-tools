"""HTTP boundary to the quant_trade provider."""

from __future__ import annotations

import os
from typing import Any, Literal

import httpx

SupportedSymbol = Literal["9984.T", "6981.T"]
SupportedInterval = Literal["1m", "5m", "15m", "1h", "1d", "1wk"]

SUPPORTED_SYMBOLS: tuple[SupportedSymbol, ...] = ("9984.T", "6981.T")
SUPPORTED_INTERVALS: tuple[SupportedInterval, ...] = (
    "1m",
    "5m",
    "15m",
    "1h",
    "1d",
    "1wk",
)
SUPPORTED_STRATEGIES = (
    "ma_cross",
    "rsi",
    "bb",
    "vwap",
    "volume",
    "combined",
    "macd",
    "pivot",
    "mfi",
    "linreg",
    "logistic",
    "knn",
    "sentiment_combo",
)
BENCHMARK_STRATEGIES = tuple(
    strategy
    for strategy in SUPPORTED_STRATEGIES
    if strategy not in {"vwap", "pivot"}
)


class QuantTradeClient:
    """Typed client for the public quant_trade market and agent APIs."""

    def __init__(
        self,
        *,
        api_base_url: str | None = None,
        agent_base_url: str | None = None,
        api_token: str | None = None,
        agent_token: str | None = None,
        timeout: float = 30.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.api_base_url = (
            api_base_url
            or os.getenv("QUANT_TRADE_API_URL")
            or os.getenv("RUST_API_URL")
            or "http://127.0.0.1:5188"
        ).rstrip("/")
        self.agent_base_url = (
            agent_base_url
            or os.getenv("QUANT_TRADE_GATEWAY_URL")
            or os.getenv("QUANT_TRADE_AGENT_URL")
            or "http://127.0.0.1:8010"
        ).rstrip("/")
        product_token = (
            api_token if api_token is not None else os.getenv("QUANT_TRADE_API_TOKEN", "")
        )
        gateway_token = agent_token if agent_token is not None else (
            os.getenv("QUANT_TRADE_AGENT_TOKEN")
            or os.getenv("TRADE_AGENT_API_TOKEN", "")
        )
        self._api_headers = self._bearer_headers(product_token)
        self._agent_headers = self._bearer_headers(gateway_token)
        self._client = httpx.Client(
            timeout=timeout,
            transport=transport,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> QuantTradeClient:
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    def quote(self, symbol: str = "9984.T") -> dict[str, Any]:
        return self._get(
            self.api_base_url,
            "/api/quote",
            params={"symbol": require_supported_symbol(symbol)},
        )

    def kline(
        self,
        interval: str = "5m",
        count: int = 100,
        *,
        symbol: str = "9984.T",
    ) -> dict[str, Any]:
        if count < 1:
            raise ValueError("count must be positive")
        payload = self._get(
            self.api_base_url,
            "/api/kline",
            params={
                "symbol": require_supported_symbol(symbol),
                "interval": require_supported_interval(interval),
            },
        )
        candles = payload.get("candles")
        if isinstance(candles, list):
            payload["candles"] = candles[-count:]
        return payload

    def signals(self, symbol: str = "9984.T") -> dict[str, Any]:
        return self._get(
            self.api_base_url,
            "/api/signals",
            params={"symbol": require_supported_symbol(symbol)},
        )

    def news(self, count: int = 10) -> dict[str, Any]:
        payload = self._get_json(
            self.api_base_url, "/api/intel/news", params={"count": count}
        )
        if not isinstance(payload, list):
            raise ValueError("quant_trade news backend must return a JSON array")
        return {"articles": payload}

    def sentiment(self) -> dict[str, Any]:
        return self._get(self.api_base_url, "/api/intel/sentiment")

    def trending(self, symbol: str = "9984.T") -> dict[str, Any]:
        return self._get(
            self.api_base_url,
            "/api/trend",
            params={"symbol": require_supported_symbol(symbol)},
        )

    def backtest(
        self,
        strategy: str,
        days: int = 60,
        *,
        symbol: str = "9984.T",
        interval: str = "5m",
        initial_cash: float | None = None,
        risk_params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        require_supported_strategy(strategy)
        if days < 1:
            raise ValueError("days must be positive")
        body: dict[str, Any] = {
            "symbol": require_supported_symbol(symbol),
            "strategy": strategy,
            "interval": require_supported_interval(interval),
            "days": days,
            "risk_params": require_risk_params(risk_params),
        }
        if initial_cash is not None:
            body["initial_cash"] = require_initial_cash(initial_cash)
        return self._post(
            self.api_base_url,
            "/api/backtest/historical",
            body,
        )

    def benchmark(
        self,
        strategy: str,
        top: int = 20,
        *,
        symbol: str = "9984.T",
        interval: str = "5m",
        initial_cash: float | None = None,
        risk_params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if strategy not in BENCHMARK_STRATEGIES:
            raise ValueError(f"Unsupported benchmark strategy: {strategy}")
        if top < 1:
            raise ValueError("top must be positive")
        body: dict[str, Any] = {
            "symbol": require_supported_symbol(symbol),
            "interval": require_supported_interval(interval),
            "risk_params": require_risk_params(risk_params),
            "use_history": True,
        }
        if initial_cash is not None:
            body["initial_cash"] = require_initial_cash(initial_cash)
        payload = self._post(
            self.api_base_url,
            "/api/backtest/benchmark",
            body,
            timeout=1800.0,
        )
        results = payload.get("results")
        if not isinstance(results, list):
            raise ValueError("quant_trade benchmark response must contain results")
        filtered = [
            result
            for result in results
            if isinstance(result, dict) and result.get("strategy_id") == strategy
        ][:top]
        payload["results"] = filtered
        payload["best_overall"] = filtered[0] if filtered else None
        return payload

    def analyze(
        self,
        *,
        symbol: str = "9984.T",
        question: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "symbol": require_supported_symbol(symbol),
            "mode": "standard",
        }
        if question is not None:
            normalized_question = question.strip()
            if not normalized_question or len(normalized_question) > 2000:
                raise ValueError("question must contain 1 to 2000 characters")
            body["question"] = normalized_question
        return self._post(
            self.agent_base_url,
            "/v1/analyze",
            body,
            headers=self._agent_headers,
        )

    def conversation_create(
        self,
        *,
        channel: str = "chat",
        symbol: str = "9984.T",
        title: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "channel": channel,
            "symbol": require_supported_symbol(symbol),
        }
        if title:
            body["title"] = title
        return self._post(self.api_base_url, "/api/conversations", body)

    def conversation_context(self, thread_id: str) -> dict[str, Any]:
        return self._get(
            self.api_base_url,
            f"/api/conversations/{require_thread_id(thread_id)}/context",
        )

    def conversation_append(
        self,
        thread_id: str,
        *,
        role: str,
        content: str,
    ) -> dict[str, Any]:
        if role not in {"user", "assistant"}:
            raise ValueError(f"Unsupported conversation role: {role}")
        if not content.strip() or len(content) > 8000:
            raise ValueError("Conversation content must contain 1 to 8000 characters")
        return self._post(
            self.api_base_url,
            f"/api/conversations/{require_thread_id(thread_id)}/messages",
            {"role": role, "content": content.strip()},
        )

    def _get(
        self,
        base_url: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload = self._get_json(base_url, path, params=params)
        return self._require_object(payload)

    def _get_json(
        self,
        base_url: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> Any:
        response = self._client.get(
            f"{base_url}{path}", params=params, headers=self._api_headers
        )
        return self._decode_json(response)

    def _post(
        self,
        base_url: str,
        path: str,
        body: dict[str, Any],
        *,
        timeout: float | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        request_options = {"timeout": timeout} if timeout is not None else {}
        response = self._client.post(
            f"{base_url}{path}",
            json=body,
            headers=headers if headers is not None else self._api_headers,
            **request_options,
        )
        return self._require_object(self._decode_json(response))

    @staticmethod
    def _bearer_headers(token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"} if token else {}

    @staticmethod
    def _decode_json(response: httpx.Response) -> Any:
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _require_object(payload: Any) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise ValueError("quant_trade backend must return a JSON object")
        return payload



def require_supported_symbol(symbol: str) -> SupportedSymbol:
    if symbol not in SUPPORTED_SYMBOLS:
        raise ValueError(f"Unsupported symbol: {symbol}")
    return symbol  # type: ignore[return-value]


def require_thread_id(thread_id: str) -> str:
    normalized = thread_id.strip()
    if not normalized or len(normalized) > 128 or any(
        character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
        for character in normalized
    ):
        raise ValueError("Invalid conversation thread id")
    return normalized


def require_supported_interval(interval: str) -> SupportedInterval:
    if interval not in SUPPORTED_INTERVALS:
        raise ValueError(f"Unsupported interval: {interval}")
    return interval  # type: ignore[return-value]


def require_supported_strategy(strategy: str) -> str:
    if strategy not in SUPPORTED_STRATEGIES:
        raise ValueError(f"Unsupported strategy: {strategy}")
    return strategy


def require_risk_params(value: dict[str, Any] | None) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError("risk_params must be a JSON object")
    return value


def require_initial_cash(value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        raise ValueError("initial_cash must be positive")
    return value
