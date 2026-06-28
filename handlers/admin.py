"""
King Bot - Admin Handlers
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import ADMIN_IDS
from keyboards.inline import admin_menu
from utils.database import (
    get_all_users, get_user_count, get_stats,
    add_points, add_balance, ban_user,
    get_pending_orders, approve_order, get_pending_tasks, complete_task, save_broadcast
)

router = Router()
logger = logging.getLogger(__name__)


class AdminStates(StatesGroup):
    waiting_broadcast = State()
    waiting_points = State()
    waiting_balance = State()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ غير مصرح لك بالوصول.")
        return
    await message.answer(
        f"🛠 <b>لوحة تحكم الأدمن</b>\n\nاختر خياراً:",
        reply_markup=admin_menu()
    )


@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    stats = get_stats()
    await callback.message.edit_text(
        f"📊 <b>إحصائيات البوت</b>\n\n"
        f"👥 المستخدمين: <b>{stats['users']}</b>\n"
        f"📱 الأرقام النشطة: <b>{stats['active_numbers']}</b>\n"
        f"📋 المهام المعلقة: <b>{stats['pending_tasks']}</b>\n"
        f"👤 طلبات الرشق: <b>{stats['pending_boosts']}</b>\n"
        f"💰 طلبات الإيداع: <b>{stats['pending_orders']}</b>\n"
        f"💵 إجمالي الإيداعات: <b>${stats['total_deposits']:.2f}</b>",
        reply_markup=admin_menu()
    )


@router.callback_query(F.data == "admin_users")
async def admin_users(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    users = get_all_users()
    if not users:
        await callback.message.edit_text("👥 لا يوجد مستخدمين بعد.", reply_markup=admin_menu())
        return

    text = "👥 <b>قائمة المستخدمين:</b>\n\n"
    for u in users[:20]:
        text += (
            f"🆔 <code>{u['user_id']}</code> | "
            f"👤 {u['username'] or '—'} | "
            f"🎯 {u['points']}⬿ | "
            f"💰 ${u['balance']:.2f}\n"
        )
    if len(users) > 20:
        text += f"\n... +{len(users) - 20} آخرين"

    await callback.message.edit_text(text, reply_markup=admin_menu(), parse_mode="HTML")


@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await callback.message.edit_text(
        "📢 أرسل الرسالة للإذاعة:\n\n"
        "⚠️ سيتم إرسالها لكل المستخدمين"
    )
    await state.set_state(AdminStates.waiting_broadcast)


@router.message(AdminStates.waiting_broadcast)
async def process_broadcast(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    users = get_all_users()
    success = 0
    failed = 0

    for user in users:
        try:
            await message.bot.send_message(user["user_id"], f"📢 <b>رسالة من الإدارة:</b>\n\n{message.text}")
            success += 1
        except Exception:
            failed += 1

    save_broadcast(message.from_user.id, message.text, success)
    await state.clear()
    await message.answer(
        f"✅ <b>تم الإذاعة!</b>\n\n"
        f"✅ نجح: {success} | ❌ فشل: {failed}",
        reply_markup=admin_menu()
    )


@router.callback_query(F.data == "admin_orders")
async def admin_orders(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    orders = get_pending_orders()
    if not orders:
        await callback.message.edit_text("📋 لا توجد طلبات معلقة.", reply_markup=admin_menu())
        return

    text = "📋 <b>طلبات الإيداع المعلقة:</b>\n\n"
    for o in orders[:10]:
        text += (
            f"📋 #{o['id']} | "
            f"👤 <code>{o['user_id']}</code> | "
            f"💰 ${o['amount']:.2f} | "
            f"📝 {o['description']}\n"
        )

    # Approve buttons
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(row_width=1)
    for o in orders[:10]:
        kb.add(InlineKeyboardButton(
            f"✅ تأكيد #{o['id']} - ${o['amount']:.2f}",
            callback_data=f"approve_order_{o['id']}"
        ))
    kb.add(InlineKeyboardButton("🔙 رجوع", callback_data="admin_orders"))

    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data.startswith("approve_order_"))
async def approve_order_handler(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    order_id = int(callback.data.split("_")[2])
    result = approve_order(order_id)

    if result["success"]:
        await callback.answer(f"✅ تم تأكيد الطلب +${result['amount']:.2f}", show_alert=True)
        # Notify user
        try:
            await callback.message.bot.send_message(
                result["user_id"],
                f"✅ <b>تم تأكيد إيداعك!</b>\n\n"
                f"💰 المبلغ: ${result['amount']:.2f}\n"
                f"📋 الطلبية: #{order_id}"
            )
        except Exception:
            pass
        await admin_orders(callback)
    else:
        await callback.answer(f"❌ {result['error']}", show_alert=True)


@router.callback_query(F.data == "admin_add_points")
async def admin_add_points_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await callback.message.edit_text(
        "➕ إضافة نقاط:\n\n"
        "أرسل: ID المستخدم عدد_النقاط\n"
        "مثال: 123456789 50"
    )
    await state.set_state(AdminStates.waiting_points)


@router.message(AdminStates.waiting_points)
async def process_add_points(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    parts = message.text.strip().split()
    if len(parts) < 2 or not parts[0].isdigit() or not parts[1].isdigit():
        await message.answer("❌ خطأ! الصيغة: ID عدد_النقاط")
        return

    user_id, points = int(parts[0]), int(parts[1])
    add_points(user_id, points)
    await state.clear()

    # Notify user
    try:
        await message.bot.send_message(user_id, f"🎯 <b>تم إضافة {points} نقطة لحسابك!</b>")
    except Exception:
        pass

    await message.answer(f"✅ تم إضافة {points} نقطة للمستخدم {user_id}", reply_markup=admin_menu())


@router.callback_query(F.data == "admin_add_balance")
async def admin_add_balance_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await callback.message.edit_text(
        "💰 إضافة رصيد:\n\n"
        "أرسل: ID المستخدم المبلغ\n"
        "مثال: 123456789 25.50"
    )
    await state.set_state(AdminStates.waiting_balance)


@router.message(AdminStates.waiting_balance)
async def process_add_balance(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    parts = message.text.strip().split()
    if len(parts) < 2:
        await message.answer("❌ خطأ! الصيغة: ID المبلغ")
        return

    try:
        user_id = int(parts[0])
        amount = float(parts[1])
    except ValueError:
        await message.answer("❌ خطأ في الأرقام!")
        return

    add_balance(user_id, amount)
    await state.clear()

    # Notify user
    try:
        await message.bot.send_message(user_id, f"💰 <b>تم إضافة ${amount:.2f} لرصيدك!</b>")
    except Exception:
        pass

    await message.answer(f"✅ تم إضافة ${amount:.2f} للمستخدم {user_id}", reply_markup=admin_menu())


@router.callback_query(F.data == "admin_tasks")
async def admin_tasks(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    tasks = get_pending_tasks()
    if not tasks:
        await callback.message.edit_text("📝 لا توجد مهام معلقة.", reply_markup=admin_menu())
        return

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    text = "📝 <b>المهام المعلقة:</b>\n\n"
    kb = InlineKeyboardMarkup(row_width=2)
    for t in tasks[:10]:
        text += (
            f"📋 #{t['id']} | "
            f"👤 {t['user_id']} | "
            f"🎯 +{t['points_reward']} | "
            f"📝 {t['task_type']}\n"
        )
        kb.add(InlineKeyboardButton(
            f"✅ تأكيد #{t['id']}",
            callback_data=f"confirm_task_{t['id']}"
        ))

    kb.add(InlineKeyboardButton("🔙 رجوع", callback_data="admin_stats"))
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data.startswith("confirm_task_"))
async def confirm_task_handler(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    task_id = int(callback.data.split("_")[2])
    result = complete_task(task_id)

    if result["success"]:
        await callback.answer(f"✅ تم إضافة {result['points']} نقطة", show_alert=True)
        # Notify user
        try:
            await callback.message.bot.send_message(
                result["user_id"],
                f"🎯 <b>تم إضافة {result['points']} نقطة!</b>\n\n"
                f"📋 المهمة: #{task_id}"
            )
        except Exception:
            pass
        await admin_tasks(callback)
    else:
        await callback.answer(f"❌ {result['error']}", show_alert=True)


@router.callback_query(F.data == "admin_close")
async def admin_close(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    await callback.message.delete()
