import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TypedDict


class TrendJson(TypedDict, total=False):
    error: str
    current_price: float
    moving_averages: Dict[str, float | str]
    rsi: float | str
    rsi_signal: str
    volume_trend: Dict[str, float | str]
    support_levels: List[float]
    resistance_levels: List[float]
    overall_trend: str
    timestamp: str


logger = logging.getLogger("logger")


def _calculate_sma(values: List[float], period: int) -> Optional[float]:
    if period <= 0 or len(values) < period:
        return None
    return sum(values[-period:]) / period


def _calculate_rsi(prices: List[float], period: int = 14) -> Optional[float]:
    if period <= 0 or len(prices) < period + 1:
        return None

    gains = 0.0
    losses = 0.0
    for idx in range(len(prices) - period, len(prices)):
        change = prices[idx] - prices[idx - 1]
        if change > 0:
            gains += change
        else:
            losses += abs(change)

    avg_gain = gains / period
    avg_loss = losses / period
    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def _find_support_resistance(prices: List[float], window: int = 5) -> List[Dict[str, Any]]:
    if window <= 0 or len(prices) < (2 * window) + 1:
        return []

    levels: List[Dict[str, Any]] = []
    for idx in range(window, len(prices) - window):
        current = prices[idx]
        is_support = all(
            prices[j] >= current for j in range(idx - window, idx + window + 1) if j != idx
        )
        is_resistance = all(
            prices[j] <= current for j in range(idx - window, idx + window + 1) if j != idx
        )

        if is_support:
            levels.append({"type": "support", "price": current, "index": idx})
        if is_resistance:
            levels.append({"type": "resistance", "price": current, "index": idx})

    return levels


def _quotation_to_float(quotation: Optional[Dict[str, Any]]) -> float:
    if not quotation:
        return 0.0
    return float(quotation.get("units", 0)) + float(quotation.get("nano", 0)) / 1_000_000_000


def _normalize_candles(payload: Any) -> List[Dict[str, float | int]]:
    """Приводит сырые свечи Tinkoff (units/nano, volume как str) к списку с float/int."""
    if not payload:
        return []

    candles = payload.get("candles") if isinstance(payload, dict) else payload
    if not isinstance(candles, list):
        return []

    normalized: List[Dict[str, float | int]] = []
    for candle in candles:
        close = _quotation_to_float(candle.get("close")) if isinstance(candle, dict) else 0.0
        volume_raw = candle.get("volume") if isinstance(candle, dict) else 0
        if isinstance(volume_raw, (int, float, str)):
            try:
                volume = int(volume_raw)
            except (TypeError, ValueError):
                volume = 0
        else:
            volume = 0
        normalized.append({"close": close, "volume": volume})
    return normalized


def analyse_stock_trends(raw_data: Any) -> TrendJson:
    normalized = _normalize_candles(raw_data)
    if not normalized:
        logger.warning("No stock data available for analysis")
        return {"error": "No stock data available"}

    prices = [item.get("close", 0) for item in normalized]
    volumes = [item.get("volume", 0) for item in normalized]
    if not prices:
        logger.warning("No price data available for analysis")
        return {"error": "No price data available"}

    current_price = prices[-1]
    sma20 = _calculate_sma(prices, 20)
    sma50 = _calculate_sma(prices, 50)
    sma200 = _calculate_sma(prices, 200)
    rsi_value = _calculate_rsi(prices, 14)

    avg_volume20 = _calculate_sma(volumes, 20)
    current_volume = volumes[-1] if volumes else 0
    volume_trend = ((current_volume - avg_volume20) / avg_volume20 * 100) if avg_volume20 else 0.0

    support_resistance = _find_support_resistance(prices)
    recent_support = [level for level in support_resistance if level["type"] == "support"][-3:]
    recent_resistance = [level for level in support_resistance if level["type"] == "resistance"][
        -3:
    ]

    trend = "Neutral"
    if sma20 and sma50:
        if current_price > sma20 > sma50:
            trend = "Bullish"
        elif current_price < sma20 < sma50:
            trend = "Bearish"

    rsi_signal = "Neutral"
    if rsi_value is not None:
        if rsi_value > 70:
            rsi_signal = "Overbought"
        elif rsi_value < 30:
            rsi_signal = "Oversold"

    volume_signal = "Normal"
    if volume_trend > 50:
        volume_signal = "High Volume (Bullish)"
    elif volume_trend < -50:
        volume_signal = "Low Volume (Bearish)"

    analysis: TrendJson = {
        "current_price": current_price,
        "moving_averages": {
            "sma20": round(sma20, 2) if sma20 is not None else "N/A",
            "sma50": round(sma50, 2) if sma50 is not None else "N/A",
            "sma200": round(sma200, 2) if sma200 is not None else "N/A",
        },
        "rsi": round(rsi_value, 2) if rsi_value is not None else "N/A",
        "rsi_signal": rsi_signal,
        "volume_trend": {
            "current": current_volume,
            "average20_day": round(avg_volume20, 0) if avg_volume20 is not None else "N/A",
            "percent_change": f"{volume_trend:.2f}%",
            "signal": volume_signal,
        },
        "support_levels": [round(level["price"], 2) for level in recent_support],
        "resistance_levels": [round(level["price"], 2) for level in recent_resistance],
        "overall_trend": trend,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    logger.debug(
        "Analysis computed: trend=%s rsi=%s volume_signal=%s",
        trend,
        analysis["rsi"],
        analysis["volume_trend"]["signal"],
    )
    return analysis
