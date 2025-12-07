import json
from typing import Any, Dict, List

import pytest
from fastapi.testclient import TestClient

from src.api.dependencies import get_tinkoff_client
from src.main import app


class _FakeTinkoffClient:
    def resolve_share_figi(
        self, *, ticker: str, figi: str | None = None, class_code: str = "TQBR"
    ) -> str:
        return f"FIGI_{ticker}"

    def get_candles(
        self,
        *,
        figi: str,
        time_from: Any,
        time_to: Any,
        interval: str = "CANDLE_INTERVAL_DAY",
    ) -> List[Dict[str, Any]]:
        base_price = 100.0
        return [
            {"close": {"units": base_price + idx, "nano": 0}, "volume": 1_000 + idx}
            for idx in range(40)
        ]


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    def _fake_create_llm() -> object:
        return object()

    async def _fake_invoke(*_: Any, **__: Any) -> str:
        return "AI ANALYSIS: bullish trend"

    monkeypatch.setattr("src.api.router.create_gigachat_llm", _fake_create_llm)
    monkeypatch.setattr("src.api.router.invoke_gigachat_with_system_prompt", _fake_invoke)

    app.dependency_overrides[get_tinkoff_client] = lambda: _FakeTinkoffClient()

    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_trends_ai_returns_plain_text(client: TestClient) -> None:
    payload = {
        "tickers": ["SBER"],
        "classCode": "TQBR",
        "days": 5,
        "interval": "CANDLE_INTERVAL_DAY",
    }

    response = client.post("/api/stock-ai/trends/ai", json=payload)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "AI ANALYSIS" in response.text


def test_trends_ai_requires_tickers(client: TestClient) -> None:
    response = client.post("/api/stock-ai/trends/ai", json={"tickers": []})

    assert response.status_code == 400
    body = json.loads(response.text)
    assert body["detail"] == "tickers must be provided"
