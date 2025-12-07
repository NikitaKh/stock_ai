import logging
import logging.config

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.router import api_router
from src.core.logging.config import LOGGING_CONFIG
from src.settings import settings

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger("logger")

app = FastAPI(
    title=settings.service_name,
    description=settings.service_description,
    openapi_url=f"{settings.api_v1_str}/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_v1_str)
logger.info(f"Приложение {settings.service_name} инициализировано")
logger.info(f"API доступен по адресу: {settings.api_v1_str}")
