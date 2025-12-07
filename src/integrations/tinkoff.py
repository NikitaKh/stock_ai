import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

from src.settings import settings

logger = logging.getLogger("logger")


class TinkoffClient:
    """Минимальный клиент Tinkoff Invest API для загрузки свечей."""

    _SHARE_BY_PATH = "tinkoff.public.invest.api.contract.v1.InstrumentsService/ShareBy"
    _GET_CANDLES_PATH = "tinkoff.public.invest.api.contract.v1.MarketDataService/GetCandles"
    _SHARES_PATH = "tinkoff.public.invest.api.contract.v1.InstrumentsService/Shares"

    def __init__(
        self,
        token: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
    ) -> None:
        self.base_url = (base_url or settings.tinkoff_base_url).rstrip("/")
        self.token = token or settings.tinkoff_api_token
        self.timeout = timeout_seconds or settings.tinkoff_timeout

        if not self.token or "TINKOFF_API_TOKEN" in self.token:
            raise ValueError("Tinkoff API token is not configured")

    def resolve_share_figi(
        self,
        *,
        ticker: Optional[str] = None,
        figi: Optional[str] = None,
        class_code: str = "TQBR",
    ) -> str:
        """Возвращает FIGI по тикеру или валидирует переданный FIGI."""
        if figi:
            return figi
        if not ticker:
            raise ValueError("ticker or figi must be provided")

        payload: Dict[str, Any] = {
            "id": ticker,
            "idType": "INSTRUMENT_ID_TYPE_TICKER",
            "classCode": class_code,
        }
        data = self._post(self._SHARE_BY_PATH, payload)
        instrument = data.get("instrument") or {}
        figi_value = instrument.get("figi")
        if not figi_value:
            raise RuntimeError(f"FIGI not found for ticker={ticker}, class_code={class_code}")
        logger.debug(
            "Resolved FIGI for ticker=%s, class_code=%s: %s", ticker, class_code, figi_value
        )
        return figi_value

    def get_candles(
        self,
        *,
        figi: str,
        time_from: datetime,
        time_to: datetime,
        interval: str = "CANDLE_INTERVAL_HOUR",
    ) -> List[Dict[str, Any]]:
        """Получает свечи по FIGI за период."""
        if not figi:
            raise ValueError("figi is required")
        if time_from >= time_to:
            raise ValueError("time_from must be earlier than time_to")

        payload = {
            "figi": figi,
            "from": time_from.astimezone(timezone.utc).isoformat(),
            "to": time_to.astimezone(timezone.utc).isoformat(),
            "interval": interval,
        }
        data = self._post(self._GET_CANDLES_PATH, payload)
        candles = data.get("candles") or []
        logger.debug("Fetched %s candles for figi=%s interval=%s", len(candles), figi, interval)
        return candles

    def _map_candle_to_trading_json(self, candle: Dict[str, Any]) -> Dict[str, Any]:
        close_value = self._quotation_to_float(candle.get("close"))
        volume_value = candle.get("volume", 0)
        return {"json": {"close": close_value, "volume": volume_value}}

    @staticmethod
    def _quotation_to_float(quotation: Optional[Dict[str, Any]]) -> float:
        if not quotation:
            return 0.0
        units = quotation.get("units", 0)
        nano = quotation.get("nano", 0)
        return float(units) + float(nano) / 1_000_000_000

    def list_shares(
        self,
        *,
        class_code: str = "TQBR",
        country_of_risk: str = "RU",
        exchange: str = "moex_mrng_evng_e_wknd_dlr",
        instrument_status: str = "INSTRUMENT_STATUS_BASE",
        instrument_exchange: str = "INSTRUMENT_EXCHANGE_UNSPECIFIED",
    ) -> List[Dict[str, Any]]:
        """
        Возвращает список акций с фильтрами по classCode, countryOfRisk, exchange.
        """
        payload = {"instrumentStatus": instrument_status, "instrumentExchange": instrument_exchange}
        data = self._post(self._SHARES_PATH, payload)
        instruments = data.get("instruments") or []
        logger.debug("Fetched %s instruments for class_code=%s", len(instruments), class_code)

        def _match(value: Optional[str], expected: Optional[str]) -> bool:
            if expected is None:
                return True
            return str(value).lower() == str(expected).lower()

        return [
            instrument
            for instrument in instruments
            if _match(instrument.get("classCode"), class_code)
            and _match(instrument.get("countryOfRisk"), country_of_risk)
            and _match(instrument.get("exchange"), exchange)
        ]

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        headers = {"Authorization": f"Bearer {self.token}"}

        with httpx.Client(timeout=self.timeout, verify=False) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        # Ответы gRPC-gateway содержат тело в поле payload
        if isinstance(data, dict) and "payload" in data:
            return data["payload"] or {}
        return data if isinstance(data, dict) else {}
