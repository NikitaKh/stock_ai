.PHONY: help install install-dev clean run run-dev format format-check lint type-check test test-cov test-fast init shell deps-update deps-export info

# Переменные
PYTHON := python3
PIP := pip3
POETRY := poetry
APP_DIR := src
TESTS_DIR := tests
LOG_DIR := log

# Цвета для вывода
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
RED := \033[0;31m
NC := \033[0m

# =============================================================================
# ОСНОВНЫЕ КОМАНДЫ
# =============================================================================

help: ## Показать справку по командам
	@echo "$(BLUE)Stock-AI$(NC)"
	@echo "$(BLUE)=============================$(NC)"
	@echo ""
	@echo "$(GREEN)Доступные команды:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""

install: ## Установить зависимости через Poetry
	@echo "$(BLUE)Установка зависимостей через Poetry...$(NC)"
	$(POETRY) install
	@echo "$(GREEN)Зависимости установлены$(NC)"

install-dev: ## Установить зависимости для разработки
	@echo "$(BLUE)Установка зависимостей для разработки...$(NC)"
	$(POETRY) install --with dev
	@echo "$(GREEN)Зависимости для разработки установлены$(NC)"

clean: ## Очистить временные файлы
	@echo "$(BLUE)Очистка временных файлов...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf $(LOG_DIR)/*.log* 2>/dev/null || true
	rm -rf htmlcov/ .coverage coverage.xml 2>/dev/null || true
	rm -rf bandit-report.json safety-report.json 2>/dev/null || true
	@echo "$(GREEN)Очистка завершена$(NC)"

# =============================================================================
# ЗАПУСК ПРИЛОЖЕНИЯ
# =============================================================================

run: ## Запустить приложение
	@echo "$(BLUE)Запуск приложения...$(NC)"
	$(POETRY) run uvicorn src.main:app --host 0.0.0.0 --port 8000

run-dev: ## Запустить в режиме разработки
	@echo "$(BLUE)Запуск в режиме разработки...$(NC)"
	$(POETRY) run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# =============================================================================
# ФОРМАТИРОВАНИЕ И ЛИНТИНГ
# =============================================================================

format: ## Форматировать код (Black + isort)
	@echo "$(BLUE)Форматирование кода...$(NC)"
	$(POETRY) run black $(APP_DIR) $(TESTS_DIR)
	$(POETRY) run isort $(APP_DIR) $(TESTS_DIR)
	@echo "$(GREEN)Код отформатирован$(NC)"

format-check: ## Проверить форматирование без изменений
	@echo "$(BLUE)Проверка форматирования...$(NC)"
	$(POETRY) run black --check $(APP_DIR) $(TESTS_DIR)
	$(POETRY) run isort --check-only $(APP_DIR) $(TESTS_DIR)
	@echo "$(GREEN)Форматирование корректно$(NC)"

lint: ## Запустить линтер (flake8)
	@echo "$(BLUE)Запуск линтера...$(NC)"
	$(POETRY) run flake8 $(APP_DIR) $(TESTS_DIR)
	@echo "$(GREEN)Линтинг пройден$(NC)"

type-check: ## Проверить типы (mypy)
	@echo "$(BLUE)Проверка типов...$(NC)"
	$(POETRY) run mypy $(APP_DIR)
	@echo "$(GREEN)Проверка типов завершена$(NC)"

# =============================================================================
# ТЕСТИРОВАНИЕ
# =============================================================================

test: ## Запустить тесты
	@echo "$(BLUE)Запуск тестов...$(NC)"
	$(POETRY) run pytest $(TESTS_DIR) -v

test-cov: ## Запустить тесты с покрытием
	@echo "$(BLUE)Запуск тестов с покрытием...$(NC)"
	$(POETRY) run pytest $(TESTS_DIR) --cov=$(APP_DIR) --cov-report=html --cov-report=term-missing --cov-report=xml

test-fast: ## Запустить быстрые тесты
	@echo "$(BLUE)Запуск быстрых тестов...$(NC)"
	$(POETRY) run pytest $(TESTS_DIR) -m "not slow" -v

# =============================================================================
# ИНИЦИАЛИЗАЦИЯ И УТИЛИТЫ
# =============================================================================

init: ## Полная инициализация проекта
	@echo "$(BLUE)Инициализация проекта...$(NC)"
	@mkdir -p $(LOG_DIR)
	@mkdir -p $(TESTS_DIR)
	@$(MAKE) install-dev
	@echo "$(GREEN)Проект инициализирован$(NC)"

shell: ## Запустить интерактивную оболочку Poetry
	@echo "$(BLUE)Запуск Poetry shell...$(NC)"
	$(POETRY) shell

deps-update: ## Обновить зависимости
	@echo "$(BLUE)Обновление зависимостей...$(NC)"
	$(POETRY) update
	@echo "$(GREEN)Зависимости обновлены$(NC)"

deps-export: ## Экспортировать зависимости в requirements.txt
	@echo "$(BLUE)Экспорт зависимостей...$(NC)"
	$(POETRY) export -f requirements.txt --output requirements.txt --without-hashes
	$(POETRY) export -f requirements.txt --output requirements-dev.txt --without-hashes --with dev
	@echo "$(GREEN)Зависимости экспортированы$(NC)"

# =============================================================================
# ИНФОРМАЦИЯ
# =============================================================================

info: ## Показать информацию о проекте
	@echo "$(BLUE)Информация о проекте Stock-AI:$(NC)"
	@echo "Poetry версия: $$($(POETRY) --version)"
	@echo "Python версия: $$($(PYTHON) --version)"
	@echo "Виртуальное окружение: $$($(POETRY) env info -p)"
	@echo "Установленные пакеты: $$($(POETRY) show | wc -l)"

# По умолчанию показываем справку
.DEFAULT_GOAL := help