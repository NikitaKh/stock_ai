# Stock AI

FastAPI сервис для анализа акций с теханализом и ИИ-обзорами.

## Стек
- FastAPI, Pydantic v2
- GigaChat для LLM-аналитики
- Tinkoff Invest API для данных по свечам

## Запуск
1) Установите зависимости: `make install-dev`
2) Создайте `.env` (см. переменные в `src/settings.py`, ключи GigaChat/Tinkoff обязательны).
3) Старт dev-сервера: `make run-dev`

### Базовые эндпоинты (префикс `/api/stock-ai`)
- `GET /stocks` - список акций по фильтрам.
- `POST /trends` - теханализ по тикерам.
- `POST /trends/ai` - теханализ + ИИ-обзор (ответ текст/markdown).

## Тесты и утилиты (Makefile)
- `make test` - pytest -v  
- `make test-fast` - быстрые тесты (mark not slow)  
- `make test-cov` - покрытие pytest  
- `make lint` - flake8  
- `make type-check` - mypy  
- `make format` / `make format-check` - black + isort  
- `make clean` - удалить кеши/артефакты  
- `make deps-export` - выгрузка зависимостей в requirements.txt  