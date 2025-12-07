from typing import List, Optional

from pydantic import BaseModel, Field


class StockFilters(BaseModel):
    class_code: str = Field(default="TQBR", alias="classCode")
    country_of_risk: str = Field(default="RU", alias="countryOfRisk")
    exchange: str = Field(default="moex_mrng_evng_e_wknd_dlr")
    instrument_status: str = Field(default="INSTRUMENT_STATUS_BASE", alias="instrumentStatus")
    instrument_exchange: str = Field(
        default="INSTRUMENT_EXCHANGE_UNSPECIFIED", alias="instrumentExchange"
    )


class ShareItem(BaseModel):
    figi: str
    ticker: Optional[str] = None
    classCode: Optional[str] = None
    isin: Optional[str] = None
    name: Optional[str] = None
    currency: Optional[str] = None
    exchange: Optional[str] = None
    countryOfRisk: Optional[str] = None
    sector: Optional[str] = None
    lot: Optional[int] = None
    shortEnabledFlag: Optional[bool] = None
    apiTradeAvailableFlag: Optional[bool] = None
    liquidityFlag: Optional[bool] = None


class StocksResponse(BaseModel):
    items: List[ShareItem]
