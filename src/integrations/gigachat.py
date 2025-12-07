import logging
from typing import Optional

from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole

from src.settings import settings

logger = logging.getLogger("logger")


def create_gigachat_llm() -> GigaChat:
    """Создает экземпляр GigaChat LLM с настройками по умолчанию."""
    return _create_gigachat_instance(
        model=settings.gigachat_model,
        timeout=settings.timeout,
        verify_ssl_certs=settings.verify_ssl_certs,
    )


def _create_gigachat_instance(
    model: str,
    timeout: int,
    verify_ssl_certs: bool,
) -> GigaChat:
    """Создает экземпляр GigaChat."""

    if not settings.gigachat_api_key or not settings.gigachat_scope:
        raise ValueError(
            "Отсутствуют обязательные параметры: GIGACHAT_API_KEY или GIGACHAT_SCOPE",
        )

    try:
        llm = GigaChat(
            scope=settings.gigachat_scope,
            credentials=settings.gigachat_api_key,
            model=model,
            verify_ssl_certs=verify_ssl_certs,
            timeout=timeout,
        )
    except Exception as exc:
        error_msg = f"Ошибка создания GigaChat LLM: {exc}"
        logger.error(error_msg, exc_info=True)
        raise RuntimeError(error_msg) from exc

    logger.info("GigaChat LLM создан: модель=%s", model)
    return llm


async def invoke_gigachat_with_system_prompt(
    llm: GigaChat,
    user_message: str,
    system_prompt: str,
    attachment: Optional[str] = None,
    temperature: Optional[float] = None,
) -> str:
    """
    Вызов GigaChat с системным промптом.

    Args:
        llm: Экземпляр GigaChat
        user_message: Сообщение пользователя
        system_prompt: Системный промпт для контекста
        attachment: uuid документа

    Returns:
        str: Ответ от модели

    Raises:
        ValueError: При некорректных входных данных
        RuntimeError: При ошибке вызова модели
    """

    if not user_message or not user_message.strip():
        raise ValueError("Сообщение пользователя не может быть пустым")

    if not system_prompt or not system_prompt.strip():
        raise ValueError("Системный промпт не может быть пустым")

    payload = Chat(
        messages=[
            Messages(role=MessagesRole.SYSTEM, content=system_prompt),
            Messages(
                role=MessagesRole.USER,
                content=user_message,
                attachments=[attachment] if attachment else None,
            ),
        ],
        temperature=temperature if temperature is not None else settings.temperature,
    )

    try:
        response = await llm.achat(payload)
        result = (
            response.choices[0].message.content if hasattr(response, "choices") else str(response)
        )
    except Exception as exc:
        error_msg = f"Ошибка вызова GigaChat с системным промптом: {exc}"
        logger.error(error_msg, exc_info=True)
        raise RuntimeError(error_msg) from exc

    if not result:
        raise RuntimeError("Получен пустой ответ от модели")

    logger.debug(
        "GigaChat ответ с системным промптом получен, длина: %s символов",
        len(result),
    )
    return result.strip()
