"""
King Bot - Keyboards
All inline and reply keyboards (aiogram 3.x / pydantic 2.x compatible)
"""

from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)


# ========== Main Menu ==========
def main_menu():
    return ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[
            [
                KeyboardButton(text="📱 أرقام وهمية"),
                KeyboardButton(text="👥 رشق وتفاعل"),
            ],
            [
                KeyboardButton(text="💰 شحن الرصيد"),
                KeyboardButton(text="👤 حسابي"),
            ],
            [
                KeyboardButton(text="📢 قناة البوت"),
                KeyboardButton(text="📞 تواصل مع المطور"),
            ],
        ]
    )


# ========== Virtual Numbers ==========
def numbers_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💎 الفئة الأولى ($10)", callback_data="num_tier1")],
            [InlineKeyboardButton(text="🥈 الفئة الثانية ($7)", callback_data="num_tier2")],
            [InlineKeyboardButton(text="� الفئة الثالثة ($5)", callback_data="num_tier3")],
            [InlineKeyboardButton(text="📱 أرقامي (الأرقام المشتراة)", callback_data="my_numbers")],
            [InlineKeyboardButton(text="� رجوع", callback_data="back_main")],
        ]
    )


def countries_menu(tier: str):
    from utils.fivesim import COUNTRIES
    countries = COUNTRIES[tier]["countries"]
    rows = []
    items = list(countries.items())
    for i in range(0, len(items), 2):
        row = []
        for code, name in items[i:i+2]:
            row.append(InlineKeyboardButton(text=name, callback_data=f"buy_{code}_{tier}"))
        rows.append(row)
    rows.append([InlineKeyboardButton(text="🔙 رجوع", callback_data="back_numbers")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def number_actions_kb(order_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📩 استقبال الكود", callback_data=f"check_sms_{order_id}"),
                InlineKeyboardButton(text="❌ إلغاء واسترداد", callback_data=f"cancel_num_{order_id}"),
            ],
            [InlineKeyboardButton(text="🔙 رجوع", callback_data="back_numbers")],
        ]
    )


def my_numbers_kb(numbers: list):
    rows = []
    for num in numbers:
        status = "✅" if num["status"] == "active" else "❌"
        rows.append([
            InlineKeyboardButton(
                text=f"{status} {num['phone_number']} - {num['country_name']}",
                callback_data=f"num_detail_{num['id']}"
            )
        ])
    rows.append([InlineKeyboardButton(text="� رجوع", callback_data="back_numbers")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ========== Boost Menu ==========
def boost_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="� اكسب نقاط (مجاني)", callback_data="earn_points")],
            [InlineKeyboardButton(text="👥 رشق متابعين (-10 نقاط)", callback_data="boost_followers")],
            [InlineKeyboardButton(text="❤️ رشق إعجابات (-5 نقاط)", callback_data="boost_likes")],
            [InlineKeyboardButton(text="� رشق مشاهدات (-3 نقاط)", callback_data="boost_views")],
            [InlineKeyboardButton(text="📋 طلباتي", callback_data="my_boosts")],
            [InlineKeyboardButton(text="🔙 رجوع", callback_data="back_main")],
        ]
    )


def earn_points_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❤️ إعجاب بمنشور (+1 نقطة)", callback_data="task_like")],
            [InlineKeyboardButton(text="� اشتراك في قناة (+2 نقطة)", callback_data="task_subscribe")],
            [InlineKeyboardButton(text="🔙 رجوع", callback_data="back_boost")],
        ]
    )


def boost_confirm_kb(boost_type: str, target: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ تأكيد", callback_data=f"confirm_{boost_type}"),
                InlineKeyboardButton(text="❌ إلغاء", callback_data="back_boost"),
            ],
        ]
    )


# ========== Balance Menu ==========
def balance_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="� عنوان المحفظة (USDT TRC20)", callback_data="show_wallet")],
            [InlineKeyboardButton(text="✅ تأكيد الدفع", callback_data="confirm_deposit")],
            [InlineKeyboardButton(text="💰 سجل العمليات", callback_data="balance_history")],
            [InlineKeyboardButton(text="🔙 رجوع", callback_data="back_main")],
        ]
    )


# ========== Admin Panel ==========
def admin_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="� الإحصائيات", callback_data="admin_stats"),
                InlineKeyboardButton(text="� المستخدمين", callback_data="admin_users"),
            ],
            [
                InlineKeyboardButton(text="📢 إذاعة", callback_data="admin_broadcast"),
                InlineKeyboardButton(text="📋 الطلبات", callback_data="admin_orders"),
            ],
            [
                InlineKeyboardButton(text="➕ إضافة نقاط", callback_data="admin_add_points"),
                InlineKeyboardButton(text="➕ إضافة رصيد", callback_data="admin_add_balance"),
            ],
            [
                InlineKeyboardButton(text="📝 المهام المعلقة", callback_data="admin_tasks"),
                InlineKeyboardButton(text="� إغلاق", callback_data="admin_close"),
            ],
        ]
    )


# ========== Contact ==========
def contact_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💬 تيليجرام", callback_data="contact_telegram")],
            [InlineKeyboardButton(text="🔙 رجوع", callback_data="back_main")],
        ]
    )
