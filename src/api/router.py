import json
import logging
from datetime import datetime, timedelta, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse

from src.api.dependencies import get_tinkoff_client
from src.integrations.gigachat import create_gigachat_llm, invoke_gigachat_with_system_prompt
from src.integrations.tinkoff import TinkoffClient
from src.schemas.stocks import ShareItem, StockFilters, StocksResponse
from src.schemas.trends import TrendResult, TrendsRequest, TrendsResponse
from src.services.trading import analyse_stock_trends
from src.settings import settings

api_router = APIRouter()
logger = logging.getLogger("logger")


@api_router.get("/stocks", response_model=StocksResponse)
def list_stocks(
    filters: StockFilters = Depends(),
    client: TinkoffClient = Depends(get_tinkoff_client),
) -> StocksResponse:
    try:
        raw_items = client.list_shares(
            class_code=filters.class_code,
            country_of_risk=filters.country_of_risk,
            exchange=filters.exchange,
            instrument_status=filters.instrument_status,
            instrument_exchange=filters.instrument_exchange,
        )
        items = [ShareItem(**item) for item in raw_items]
    except Exception as exc:
        logger.error("Failed to fetch shares: %s", exc, exc_info=True)
        raise HTTPException(status_code=502, detail=f"Failed to fetch shares: {exc}") from exc

    logger.info("Fetched %s shares for class_code=%s", len(items), filters.class_code)
    return StocksResponse(items=items)


@api_router.post("/trends", response_model=TrendsResponse)
def analyse_trends(
    payload: TrendsRequest,
    client: TinkoffClient = Depends(get_tinkoff_client),
) -> TrendsResponse:
    if not payload.tickers:
        raise HTTPException(status_code=400, detail="tickers must be provided")

    results: List[TrendResult] = []

    try:
        for ticker in payload.tickers:
            resolved_figi = client.resolve_share_figi(
                ticker=ticker,
                figi=None,
                class_code=payload.class_code,
            )
            time_to = datetime.now(timezone.utc)
            time_from = time_to - timedelta(days=payload.days)
            candles = client.get_candles(
                figi=resolved_figi,
                time_from=time_from,
                time_to=time_to,
                interval=payload.interval,
            )
            analysis = analyse_stock_trends({"candles": candles})
            results.append(TrendResult(figi=resolved_figi, ticker=ticker, analysis=dict(analysis)))
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to analyse trends: %s", exc, exc_info=True)
        raise HTTPException(status_code=502, detail=f"Failed to analyse trends: {exc}") from exc

    if not results:
        raise HTTPException(status_code=404, detail="No data found for provided instruments")

    logger.info("Analysed trends for %s tickers", len(results))
    return TrendsResponse(results=results)


@api_router.post("/trends/ai", response_class=PlainTextResponse)
async def analyse_trends_ai(
    payload: TrendsRequest,
    client: TinkoffClient = Depends(get_tinkoff_client),
) -> PlainTextResponse:
    if not payload.tickers:
        raise HTTPException(status_code=400, detail="tickers must be provided")

    results: List[TrendResult] = []

    try:
        for ticker in payload.tickers:
            resolved_figi = client.resolve_share_figi(
                ticker=ticker,
                figi=None,
                class_code=payload.class_code,
            )
            time_to = datetime.now(timezone.utc)
            time_from = time_to - timedelta(days=payload.days)
            candles = client.get_candles(
                figi=resolved_figi,
                time_from=time_from,
                time_to=time_to,
                interval=payload.interval,
            )
            analysis = analyse_stock_trends({"candles": candles})
            results.append(TrendResult(figi=resolved_figi, ticker=ticker, analysis=dict(analysis)))
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to analyse trends: %s", exc, exc_info=True)
        raise HTTPException(status_code=502, detail=f"Failed to analyse trends: {exc}") from exc

    if not results:
        raise HTTPException(status_code=404, detail="No data found for provided instruments")

    llm = create_gigachat_llm()
    trends_json = json.dumps(
        [result.model_dump() for result in results], ensure_ascii=False, indent=2
    )
    user_prompt = settings.user_prompt.format(JSON_DATA=trends_json)

    try:
        ai_analysis = await invoke_gigachat_with_system_prompt(
            llm=llm,
            user_message=user_prompt,
            system_prompt=settings.system_prompt,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Failed to get AI trend analysis: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=502, detail=f"Failed to get AI trend analysis: {exc}"
        ) from exc

    logger.info("AI analysed trends for %s tickers", len(results))
    return PlainTextResponse(content=ai_analysis, media_type="text/plain; charset=utf-8")
