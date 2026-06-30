"""
King Bot - Main Entry Point (Webhook)
Compatible with: aiogram 3.12, pydantic 2.x, Render free web service
"""

import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN, WEBHOOK_PATH, WEBHOOK_SECRET, SERVER_HOST, SERVER_PORT
from middleware.subscription import SubscriptionMiddleware
from handlers.user import router as user_router
from handlers.admin import router as admin_router
from models import init_db


# === Logging ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# === Bot / Dispatcher ===
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# === Subscription Middleware ===
# Registered globally — runs before every message and callback
# Checks channel membership, blocks non-subscribers with a prompt
sub_middleware = SubscriptionMiddleware()
dp.message.middleware(sub_middleware)
dp.callback_query.middleware(sub_middleware)

dp.include_router(user_router)
dp.include_router(admin_router)


# === Health endpoints ===
async def handle_health(request):
    return web.json_response({"status": "ok"})


# === Webhook endpoint (handles ALL updates from Telegram) ===
async def handle_webhook(request):
    """Receive Telegram update, validate secret, feed to dispatcher."""
    # 1. Validate secret token
    incoming_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if incoming_secret != WEBHOOK_SECRET:
        logger.warning("Rejected webhook: bad secret")
        return web.Response(status=403)

    # 2. Parse JSON body into aiogram Update and feed to dispatcher
    try:
        body = await request.json()
        from aiogram.types import Update
        update = Update.model_validate(body)
        await dp.feed_webhook_update(bot, update)
    except Exception as exc:
        logger.error("Webhook exception: %s", exc)

    # Always 200 so Telegram doesn't retry
    return web.Response(text="ok", status=200)


# === Lifecycle ===
async def startup(app):
    init_db()
    logger.info("DB ready")

    render_url = os.getenv("RENDER_EXTERNAL_URL", "")
    if render_url:
        webhook_url = render_url + WEBHOOK_PATH
    else:
        webhook_url = "http://localhost:" + str(SERVER_PORT) + WEBHOOK_PATH

    try:
        await bot.set_webhook(url=webhook_url, secret_token=WEBHOOK_SECRET)
        logger.info("Webhook set: %s", webhook_url)
    except Exception as exc:
        logger.error("set_webhook failed: %s", exc)


async def shutdown(app):
    try:
        await bot.session.close()
    except Exception:
        pass


# === aiohttp app ===
def build_app():
    app = web.Application()
    app.router.add_get("/", handle_health)
    app.router.add_get("/api/health", handle_health)
    app.router.add_post(WEBHOOK_PATH, handle_webhook)
    app.on_startup.append(startup)
    app.on_shutdown.append(shutdown)
    return app


# === Entry ===
def main():
    port = int(SERVER_PORT) if isinstance(SERVER_PORT, str) else SERVER_PORT
    logger.info("King Bot starting on %s:%d", SERVER_HOST, port)
    web.run_app(build_app(), host=SERVER_HOST, port=port)


if __name__ == "__main__":
    main()
