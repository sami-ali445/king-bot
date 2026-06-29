"""
King Bot - Social Media & Virtual Numbers Bot
Project Configuration (Secure - uses environment variables)
"""

import os

# Bot
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
BOT_NAME = "King Bot"

# 5sim API
FIVE_SIM_API_KEY = os.getenv("FIVE_SIM_API_KEY", "")
FIVE_SIM_BASE_URL = "https://5sim.net/v1"

# Admin
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "8916948567,555666777").split(",") if x.strip()]
DEVELOPER_USERNAME = "@king_developer"

# Wallet
WALLET_ADDRESS = os.getenv("WALLET_ADDRESS", "TLhmbZbsvRhf2TpGiotkHnbv7YBfxbKprn")
WALLET_NETWORK = "TRC20"
WALLET_COIN = "USDT"

# Database
DB_PATH = "data/bot.db"

# Webhook
WEBHOOK_PATH = "/webhook/kingbot"
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "king_bot_2026_secure_webhook_token_xyz789")

# Server
SERVER_HOST = "0.0.0.0"
SERVER_PORT = os.getenv("PORT", "10000")
