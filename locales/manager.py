# app/locales/manager.py
from typing import Any, Callable, Dict, Awaitable, Optional
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User
from aiogram_i18n import I18nMiddleware
from app.database.crud import select_lang# Импортируйте вашу функцию

class UserMiddleware(BaseMiddleware):
    def __init__(self, i18n_middleware: I18nMiddleware):
        self.i18n_middleware = i18n_middleware
        self._cache = {}  # Простой кэш для языков пользователей
        super().__init__()

    async def _get_user_locale(self, user_id: int, user_language_code: Optional[str]) -> str:
        """Получает локаль пользователя с кэшированием"""
        if user_id in self._cache:
            return self._cache[user_id]
        
        # Пробуем получить из БД
        try:
            db_locale = await select_lang(user_id)
            if db_locale:
                self._cache[user_id] = db_locale
                return db_locale
        except Exception:
            pass
        
        # Используем язык из Telegram или дефолтный
        locale = user_language_code or "en"
        self._cache[user_id] = locale
        return locale

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        locale = "en"  # локаль по умолчанию
        
        user: User = data.get("event_from_user")
        if user:
            locale = await self._get_user_locale(
                user_id=user.id,
                user_language_code=user.language_code
            )
        
        # Создаем контекст локализации
        ctx = self.i18n_middleware.new_context(locale=locale, data=data)
        
        # Сохраняем контекст в data
        data["i18n"] = ctx
        data["locale"] = locale  # Дополнительно сохраняем локаль
        
        return await handler(event, data)