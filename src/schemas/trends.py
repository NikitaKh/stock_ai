from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class TrendsRequest(BaseModel):
    tickers: List[str] = Field(default_factory=list)
    class_code: str = Field(default="TQBR", alias="classCode")
    days: int = Field(default=60, ge=1, le=365)
    interval: str = Field(default="CANDLE_INTERVAL_DAY")

    @field_validator("tickers", mode="after")
    @classmethod
    def _strip_items(cls, value: List[str]) -> List[str]:
        return [item.strip() for item in value if item and item.strip()]

    @field_validator("interval")
    @classmethod
    def _interval_not_empty(cls, value: str) -> str:
        if not value:
            raise ValueError("interval must be provided")
        return value

    def has_instruments(self) -> bool:
        return bool(self.tickers)


class TrendResult(BaseModel):
    figi: Optional[str] = None
    ticker: Optional[str] = None
    analysis: Dict[str, Any]


class TrendsResponse(BaseModel):
    results: List[TrendResult]
