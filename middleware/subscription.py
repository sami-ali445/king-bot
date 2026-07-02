"""
King Bot - Subscription Middleware
Forces users to join the official channel before using the bot.
Uses aiogram 3.x BaseMiddleware pattern.
"""

import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Update, Message, CallbackQuery

from config import CHANNEL_USERNAME, CHANNEL_INVITE_LINK, ADMIN_IDS

logger = logging.getLogger(__name__)


class SubscriptionMiddleware(BaseMiddleware):
    """Check if user is subscribed to the official channel before processing."""

    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any],
    ) -> Any:
        # Extract user and bot from event
        bot = data.get("bot")

        # Determine user_id and send function based on event type
        user_id = None
        is_callback = False

        if event.message and event.message.from_user:
            user_id = event.message.from_user.id
        elif event.callback_query and event.callback_query.from_user:
            user_id = event.callback_query.from_user.id
            is_callback = True
        else:
            # No user info (e.g., channel_post) — skip check
            return await handler(event, data)

        # Skip check for admins
        if user_id in ADMIN_IDS:
            return await handler(event, data)

        # Skip check for /start command - always show main menu even if not subscribed
        if event.message and event.message.text and event.message.text.startswith("/start"):
            # Allow entry and send main menu response
            # We'll handle this in the cmd_start handler, just bypass middleware check
            return await handler(event, data)

        # Skip if channel not configured
        if not CHANNEL_USERNAME:
            return await handler(event, data)

        # Check subscription status
        is_member = await self._check_membership(bot, user_id)

        if is_member:
            return await handler(event, data)

        # User NOT subscribed — block and prompt
        if is_callback:
            # For callback queries, answer with alert
            try:
                await event.callback_query.answer(
                    "🔒 اشترك في القناة أولاً لتتمكن من استخدام البوت!",
                    show_alert=True,
                )
            except Exception:
                pass
            # Optionally send the subscription prompt
            try:
                await bot.send_message(
                    user_id,
                    self._prompt_text(),
                )
            except Exception:
                pass
            return  # Do NOT call handler
        else:
            # For messages, reply with prompt
            try:
                if event.message:
                    await event.message.answer(self._prompt_text())
            except Exception:
                pass
            return  # Do NOT call handler

    async def _check_membership(self, bot, user_id: int) -> bool:
        """Return True if user is a member of the channel (admin/creator/member)."""
        try:
            member = await bot.get_chat_member(
                chat_id=CHANNEL_USERNAME,
                user_id=user_id,
            )
            # status: left, kicked = NOT a member
            return member.status not in ("left", "kicked")
        except Exception as exc:
            logger.warning("get_chat_member(user=%s): %s — allowing access", user_id, exc)
            return True  # Fail open so bot stays usable if API call fails

    def _prompt_text(self) -> str:
        return (
            "🔒 <b>اشتراك القناة مطلوب!</b>\n\n"
            f"اشترك في قناتنا الرسمية أولاً:\n"
            f"📢 <a href=\"{CHANNEL_INVITE_LINK}\">{CHANNEL_USERNAME}</a>\n\n"
            "بعد الاشتراك، أرسل /start أو اضغط الزر مجدداً للمتابعة ✅"
        )
