"""
King Bot - Main Entry Point
Webhook mode for Render Web Service (free tier)
"""

import logging
import asyncio
import os
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


async def on_startup(app: web.Application):
    """Initialize DB and set webhook on startup"""
    init_db()
    
    # Determine the Render external URL
    render_url = os.getenv("RENDER_EXTERNAL_URL", "")
    if render_url:
        webhook_url = f"{render_url}{WEBHOOK_PATH}"
    else:
        # Fallback for local testing
        webhook_url = f"http://localhost:{SERVER_PORT}{WEBHOOK_PATH}"
    
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(
        url=webhook_url,
        secret_token=WEBHOOK_SECRET,
        allowed_updates=["message", "callback_query"]
    )
    logger.info(f"Webhook set to: {webhook_url}")
    logger.info("King Bot started in WEBHOOK mode!")


async def health_handler(request: web.Request):
    """Health check endpoint for Render"""
    return web.json_response({"status": "ok", "bot": "King Bot", "mode": "webhook"})


async def root_handler(request: web.Request):
    """Root endpoint"""
    return web.json_response({
        "bot": "King Bot",
        "status": "running",
        "mode": "webhook"
    })


def create_app() -> web.Application:
    """Create aiohttp application with aiogram webhook integration"""
    app = web.Application()
    
    # Health check routes
    app.router.add_get("/", root_handler)
    app.router.add_get("/api/health", health_handler)
    
    # Register startup handler
    app.on_startup.append(on_startup)
    
    # Setup aiogram webhook handler
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=WEBHOOK_SECRET,
    )
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    
    # Alternative: setup_application method
    # setup_application(app, dp, bot=bot)
    
    return app


async def main():
    """Main entry - webhook mode for Render Web Service"""
    app = create_app()
    
    # Run the aiohttp web server
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(SERVER_PORT) if isinstance(SERVER_PORT, str) else SERVER_PORT
    site = web.TCPSite(runner, host=SERVER_HOST, port=port)
    
    logger.info(f"Starting web server on {SERVER_HOST}:{port}")
    await site.start()
    
    # Keep running forever
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
