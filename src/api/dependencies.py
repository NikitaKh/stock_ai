from functools import lru_cache

from src.integrations.tinkoff import TinkoffClient


@lru_cache
def get_tinkoff_client() -> TinkoffClient:
    return TinkoffClient()
