"""
King Bot - Main Entry Point
Webhook + Polling with protection
"""

import logging
import asyncio
from aiohttp import web

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.webhook.aiohttp import SimpleRequestHandler, setup_application

from config import BOT_TOKEN, WEBHOOK_PATH, WEBHOOK_SECRET, SERVER_HOST, SERVER_PORT
from handlers.user import router as user_router
from handlers.admin import router as admin_router
from models import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
dp.include_router(user_router)
dp.include_router(admin_router)


async def on_startup():
    init_db()
    logger.info("King Bot started!")


async def webhook_handler(request: web.Request):
    """Handle incoming webhook updates from Telegram"""
    try:
        secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if secret != WEBHOOK_SECRET:
            return web.Response(status=403, text="Forbidden")

        update = await request.json()
        await dp.feed_update(bot, bot.bot)
        return web.Response(status=200, text='{"ok":true}')
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return web.Response(status=500, text="Error")


async def health_handler(request: web.Request):
    """Health check endpoint"""
    return web.json_response({"status": "ok", "bot": "King Bot"})


async def on_start(app: web.Application):
    """Set webhook on startup"""
    webhook_url = f"https://{request.host}{WEBHOOK_PATH}" if hasattr(request, 'host') else None
    await bot.set_webhook(
        url=webhook_url or f"https://king-bot.onrender.com{WEBHOOK_PATH}",
        secret_token=WEBHOOK_SECRET,
        allowed_updates=["message", "callback_query"]
    )
    logger.info(f"Webhook set to {WEBHOOK_PATH}")


def create_app() -> web.Application:
    """Create aiohttp application for webhook mode"""
    app = web.Application()
    app.router.add_get("/api/health", health_handler)
    app.router.add_post(WEBHOOK_PATH, webhook_handler)
    app.on_startup.append(lambda app: bot.set_webhook(
        url=f"https://king-bot.onrender.com{WEBHOOK_PATH}",
        secret_token=WEBHOOK_SECRET,
        allowed_updates=["message", "callback_query"]
    ))
    return app


async def main():
    """Main entry - use polling for simplicity on free tier"""
    dp.startup.register(on_startup)

    # Delete any existing webhook first
    await bot.delete_webhook(drop_pending_updates=True)

    # Start polling (more reliable on free tier)
    logger.info("Starting King Bot in polling mode...")
    await dp.start_polling(bot, allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    asyncio.run(main())
