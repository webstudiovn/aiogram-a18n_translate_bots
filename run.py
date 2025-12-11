from pathlib import Path
import asyncio
import logging
import aiohttp
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from app.config.settings import configs
from app.handlers import router as main_router
from app.utils.commands import set_commands
from aiogram_i18n import I18nMiddleware
from aiogram_i18n.cores.fluent_runtime_core import FluentRuntimeCore
from app.locales.manager import UserMiddleware
import shutil

logging.basicConfig(level=logging.INFO)

storage = MemoryStorage()
bot = Bot(token=configs.telegram.token)
dp = Dispatcher(storage=storage)

async def main() -> None:
    async with aiohttp.ClientSession() as session:
        # Очистка __pycache__ перед запуском
        for pycache in Path(__file__).parent.rglob("__pycache__"):
            shutil.rmtree(pycache, ignore_errors=True)
            print(f"Cleaned: {pycache}")
        
        BASE_DIR = Path(__file__).parent
        LOCALES_DIR = BASE_DIR / "app" / "locales"
        
        print(f"Looking for locales in: {LOCALES_DIR}")
        
        if not LOCALES_DIR.exists():
            raise FileNotFoundError(f"Locales directory not found: {LOCALES_DIR}")
        
        # Переименовываем файлы в правильную структуру
        # Стандартная структура: locales/{lang}/main.ftl
        ftl_files = list(LOCALES_DIR.glob("*.ftl"))
        print(f"Found FTL files: {ftl_files}")
        
        # Создаем структуру папок
        for ftl_file in ftl_files:
            lang = ftl_file.stem  # en, de, ru и т.д.
            lang_dir = LOCALES_DIR / lang
            lang_dir.mkdir(exist_ok=True)
            
            # Переносим файл в подпапку с именем main.ftl
            new_path = lang_dir / "main.ftl"
            if not new_path.exists():
                # Если файл уже есть в подпапке, не перезаписываем
                shutil.move(str(ftl_file), str(new_path))
                print(f"Moved {ftl_file.name} to {lang}/main.ftl")
        
        # Проверяем результат
        print("\nFinal structure:")
        for item in LOCALES_DIR.iterdir():
            if item.is_dir():
                print(f"  {item.name}/")
                for file in item.iterdir():
                    print(f"    - {file.name}")
        
        # Теперь используем стандартное ядро
        i18n = I18nMiddleware(
            core=FluentRuntimeCore(
                path=LOCALES_DIR / "{locale}",
                default_locale="en",
            )
        )
        
        i18n.setup(dp)
        
        user_middleware = UserMiddleware(i18n_middleware=i18n)
        dp.update.middleware.register(user_middleware)
        
        dp.include_router(main_router)
        await set_commands(bot)
        await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен")