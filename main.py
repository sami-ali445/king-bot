"""
King Bot - Main Entry Point
Webhook mode for Render Web Service (free tier)
Runs an aiohttp server that handles both Telegram webhooks and health checks.
"""

import logging
import asyncio
import os
from aiohttp import web

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.webhook.aiohttp import SimpleRequestHandler

from config import BOT_TOKEN, WEBHOOK_PATH, WEBHOOK_SECRET, SERVER_HOST, SERVER_PORT
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


# ── Web Handlers ──────────────────────────────────────────────────
async def health(request: web.Request) -> web.Response:
    return web.json_response({"status": "ok", "bot": "King Bot"})


# ── Startup ───────────────────────────────────────────────────────
async def on_startup(app: web.Application) -> None:
    """Init DB + set Telegram webhook."""
    # 1. Initialize database
    logger.info("on_startup – initialising DB …")
    try:
        init_db()
        logger.info("on_startup – DB initialised OK")
    except Exception as e:
        logger.error(f"on_startup – DB init error: {e}")
        # Don't crash — let the server run even if DB has issues
    
    # 3. Set Telegram webhook
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
        # Don't crash — server will still run for health checks


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

    # Plain routes
    app.router.add_get("/", health)
    app.router.add_get("/api/health", health)

    # aiogram webhook handler (handles POST on WEBHOOK_PATH)
    SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=WEBHOOK_SECRET,
    ).register(app, path=WEBHOOK_PATH)

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
