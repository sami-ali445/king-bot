"""
King Bot - Keyboards
All inline and reply keyboards
"""

from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)


# ========== Main Menu ==========
def main_menu():
    kb = ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[
            [
                KeyboardButton("📱 أرقام وهمية"),
                KeyboardButton("� رشق وتفا�ل"),
            ],
            [
                KeyboardButton("💰 شحن الرصيد"),
                KeyboardButton("📊 حسابي"),
            ],
            [
                KeyboardButton("📢 قناة البوت"),
                KeyboardButton("📞 تواصل مع المطور"),
            ],
        ]
    )
    return kb


# ========== Virtual Numbers ==========
def numbers_menu():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("💎 الفئة الأولى ($10)", callback_data="num_tier1"))
    kb.add(InlineKeyboardButton("🥈 الفئة الثانية ($7)", callback_data="num_tier2"))
    kb.add(InlineKeyboardButton("🥉 الفئة الثالثة ($5)", callback_data="num_tier3"))
    kb.add(InlineKeyboardButton("📱 أرقامي (الأرقام المشتراة)", callback_data="my_numbers"))
    kb.add(InlineKeyboardButton("🔙 رجوع", callback_data="back_main"))
    return kb


def countries_menu(tier: str):
    from utils.fivesim import COUNTRIES
    kb = InlineKeyboardMarkup(row_width=2)
    countries = COUNTRIES[tier]["countries"]
    buttons = []
    for code, name in countries.items():
        buttons.append(InlineKeyboardButton(name, callback_data=f"buy_{code}_{tier}"))
    kb.add(*buttons)
    kb.add(InlineKeyboardButton("🔙 رجوع", callback_data="back_numbers"))
    return kb


def number_actions_kb(order_id: int):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("📩 استقبال الكود", callback_data=f"check_sms_{order_id}"),
        InlineKeyboardButton("❌ إلغاء واسترداد", callback_data=f"cancel_num_{order_id}")
    )
    kb.add(InlineKeyboardButton("🔙 رجوع", callback_data="back_numbers"))
    return kb


def my_numbers_kb(numbers: list):
    kb = InlineKeyboardMarkup(row_width=1)
    for num in numbers:
        status = "✅" if num["status"] == "active" else "❌"
        kb.add(InlineKeyboardButton(
            f"{status} {num['phone_number']} - {num['country_name']}",
            callback_data=f"num_detail_{num['id']}"
        ))
    kb.add(InlineKeyboardButton("🔙 رجوع", callback_data="back_numbers"))
    return kb


# ========== Boost Menu ==========
def boost_menu():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("🎯 اكسب نقاط (مجاني)", callback_data="earn_points"))
    kb.add(InlineKeyboardButton("👥 رشق متابعين (-10 نقاط)", callback_data="boost_followers"))
    kb.add(InlineKeyboardButton("❤️ رشق إعجابات (-5 نقاط)", callback_data="boost_likes"))
    kb.add(InlineKeyboardButton("👁 رشق مشاهدات (-3 نقاط)", callback_data="boost_views"))
    kb.add(InlineKeyboardButton("📋 طلباتي", callback_data="my_boosts"))
    kb.add(InlineKeyboardButton("🔙 رجوع", callback_data="back_main"))
    return kb


def earn_points_menu():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("❤️ إعجاب بمنشور (+1 نقطة)", callback_data="task_like"))
    kb.add(InlineKeyboardButton("📢 اشتراك في قناة (+2 نقطة)", callback_data="task_subscribe"))
    kb.add(InlineKeyboardButton("🔙 رجوع", callback_data="back_boost"))
    return kb


def boost_confirm_kb(boost_type: str, target: str):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✅ تأكيد", callback_data=f"confirm_{boost_type}"),
        InlineKeyboardButton("❌ إلغاء", callback_data="back_boost")
    )
    return kb


# ========== Balance Menu ==========
def balance_menu():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("💳 عنوان المحفظة (USDT TRC20)", callback_data="show_wallet"))
    kb.add(InlineKeyboardButton("✅ تأكيد الدفع", callback_data="confirm_deposit"))
    kb.add(InlineKeyboardButton("💰 سجل العمليات", callback_data="balance_history"))
    kb.add(InlineKeyboardButton("🔙 رجوع", callback_data="back_main"))
    return kb


# ========== Admin Panel ==========
def admin_menu():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats"),
        InlineKeyboardButton("👥 المستخدمين", callback_data="admin_users"),
    )
    kb.add(
        InlineKeyboardButton("📢 إذاعة", callback_data="admin_broadcast"),
        InlineKeyboardButton("📋 الطلبات", callback_data="admin_orders"),
    )
    kb.add(
        InlineKeyboardButton("➕ إضافة نقاط", callback_data="admin_add_points"),
        InlineKeyboardButton("➕ إضافة رصيد", callback_data="admin_add_balance"),
    )
    kb.add(
        InlineKeyboardButton("📝 المهام المعلقة", callback_data="admin_tasks"),
        InlineKeyboardButton("🔙 إغلاق", callback_data="admin_close"),
    )
    return kb


# ========== Contact ==========
def contact_menu():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("💬 تيليجرام", callback_data="contact_telegram"))
    kb.add(InlineKeyboardButton("🔙 رجوع", callback_data="back_main"))
    return kb
