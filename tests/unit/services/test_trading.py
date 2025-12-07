from typing import Any, Dict, List

from src.services.trading import analyse_stock_trends


def _build_candles(count: int = 60) -> List[Dict[str, Any]]:
    return [
        {"close": {"units": 100 + idx, "nano": 0}, "volume": 1_000 + idx} for idx in range(count)
    ]


def test_analyse_stock_trends_returns_error_when_empty() -> None:
    assert analyse_stock_trends({"candles": []})["error"] == "No stock data available"


def test_analyse_stock_trends_computes_basic_metrics() -> None:
    candles = _build_candles()
    result = analyse_stock_trends({"candles": candles})

    assert result["current_price"] == 100 + 59
    assert result["moving_averages"]["sma20"] != "N/A"
    assert result["moving_averages"]["sma50"] != "N/A"
    assert result["overall_trend"] == "Bullish"
