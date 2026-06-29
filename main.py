"""
King Bot - Main Entry Point
Webhook mode for Render Web Service (free tier)
"""

import logging
import os
import json
from aiohttp import web

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Update

from config import BOT_TOKEN, WEBHOOK_PATH, WEBHOOK_SECRET, ADMIN_IDS, SERVER_HOST, SERVER_PORT
from handlers.user import router as user_router
from handlers.admin import router as admin_router
from models import init_db

# ── Logging ──────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ── Bot & Dispatcher ──────────────────────────────────────────────
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher()
dp.include_router(user_router)
dp.include_router(admin_router)


# ── Handlers ──────────────────────────────────────────────────────
async def health(request: web.Request) -> web.Response:
    return web.json_response({"status": "ok", "bot": "King Bot"})


async def telegram_webhook(request: web.Request) -> web.Response:
    """Handle incoming Telegram updates via webhook."""
    # Verify secret token
    secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if secret != WEBHOOK_SECRET:
        logger.warning("Webhook: invalid secret token received")
        return web.Response(status=403)

    try:
        body = await request.read()
        json_data = json.loads(body)
        update = Update(**json_data)
        await dp.feed_webhook_update(bot, update)
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        # Still return 200 to prevent Telegram retries
    return web.Response(status=200)


# ── Startup ───────────────────────────────────────────────────────
async def on_startup(app: web.Application) -> None:
    """Init DB + set Telegram webhook."""
    # 1. Initialize database (/tmp/bot.db on Render)
    logger.info("on_startup – initialising DB …")
    try:
        init_db()
        logger.info("on_startup – DB initialised OK")
    except Exception as e:
        logger.error(f"on_startup – DB init error: {e}")

    # 2. Set Telegram webhook
    render_url = os.getenv("RENDER_EXTERNAL_URL", "")
    if render_url:
        public_url = f"{render_url}{WEBHOOK_PATH}"
    else:
        port = int(SERVER_PORT) if isinstance(SERVER_PORT, str) else SERVER_PORT
        public_url = f"http://localhost:{port}{WEBHOOK_PATH}"

    logger.info("on_startup – setting webhook to %s", public_url)
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await bot.set_webhook(
            url=public_url,
            secret_token=WEBHOOK_SECRET,
            allowed_updates=["message", "callback_query"],
        )
        logger.info("on_startup – webhook set OK ✅")
    except Exception as e:
        logger.error(f"on_startup – webhook error: {e}")


async def on_shutdown(app: web.Application) -> None:
    logger.info("on_shutdown – closing …")
    try:
        await bot.session.close()
    except Exception:
        pass


# ── App factory ───────────────────────────────────────────────────
def create_app() -> web.Application:
    """Build the aiohttp application."""
    app = web.Application()

    # Health check routes
    app.router.add_get("/", health)
    app.router.add_get("/api/health", health)

    # Telegram webhook endpoint
    app.router.add_post(WEBHOOK_PATH, telegram_webhook)

    # Lifecycle
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    return app


# ── Entry point ───────────────────────────────────────────────────
def main() -> None:
    """Entry point for render startCommand: python main.py"""
    app = create_app()

    port = int(SERVER_PORT) if isinstance(SERVER_PORT, str) else SERVER_PORT

    logger.info("Starting King Bot – Webhook Server on %s:%d", SERVER_HOST, port)

    web.run_app(
        app,
        host=SERVER_HOST,
        port=port,
        print=logger.info,
    )


if __name__ == "__main__":
    main()
