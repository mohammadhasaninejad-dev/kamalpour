import asyncio
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN, WEBAPP_URL
from database import init_db
from handlers import start_router, search_router, admin_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def on_startup(bot: Bot):
    await init_db()
    logger.info("Database initialized")
    me = await bot.get_me()
    logger.info(f"Bot started: @{me.username}")


def create_webapp_app():
    """سرور ساده برای سرو کردن مینی‌اپ"""
    app = web.Application()

    async def scanner_page(request):
        html = open("webapp/scanner.html", "r", encoding="utf-8").read()
        # جایگزینی آدرس برگشت اگر لازم باشد
        return web.Response(text=html, content_type="text/html")

    async def health(request):
        return web.Response(text="ok")

    app.router.add_get("/scanner", scanner_page)
    app.router.add_get("/", health)
    app.router.add_get("/health", health)
    return app


async def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set")

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(start_router)
    dp.include_router(search_router)
    dp.include_router(admin_router)

    dp.startup.register(on_startup)

    # اجرای همزمان بات و وب‌سرور مینی‌اپ
    web_app = create_webapp_app()
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(__import__("os").getenv("PORT", 8080)))
    await site.start()
    logger.info(f"WebApp server started on port {__import__('os').getenv('PORT', 8080)}")

    try:
        await dp.start_polling(bot)
    finally:
        await runner.cleanup()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())