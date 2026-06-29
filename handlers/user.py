"""
King Bot - User Handlers
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import ADMIN_IDS, DEVELOPER_USERNAME, WALLET_ADDRESS, WALLET_NETWORK, WALLET_COIN
from keyboards.inline import (
    main_menu, numbers_menu, countries_menu, number_actions_kb,
    my_numbers_kb, boost_menu, earn_points_menu, balance_menu, contact_menu
)
from utils.fivesim import COUNTRIES, get_balance as get_5sim_balance, buy_number, check_sms, cancel_number, finish_order
from utils.database import (
    register_user, add_points, deduct_points, get_points, get_balance, add_balance,
    save_number, update_number_sms, cancel_number as db_cancel_number, get_user_numbers,
    get_active_number_by_order, create_task, create_boost, get_all_users, get_user_count
)

router = Router()
logger = logging.getLogger(__name__)


class States(StatesGroup):
    waiting_link = State()
    waiting_boost_target = State()
    waiting_boost_quantity = State()
    waiting_deposit_amount = State()


# ========== Start ==========
@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    register_user(user_id, message.from_user.username or "", message.from_user.full_name or "")

    welcome = (
        f"👑 <b>مرحباً بك في بوت الملك!</b>\n\n"
        f"🤖 بوت خدمات السوشيال ميديا والأرقام الوهمية\n\n"
        f"📱 <b>أرقام وهمية:</b> 3 فئات سعرية\n"
        f"👥 <b>رشق وتفاعل:</b> اكسب نقاط مجاناً وارشق قناتك\n"
        f"💰 <b>شحن الرصيد:</b> USDT عبر محفظتك\n\n"
        f"🎯 <b>نقاطك:</b> {get_points(user_id)} نقطة\n"
        f"💰 <b>رصيدك:</b> ${get_balance(user_id):.2f}\n\n"
        f"⬇️ اختر من القائمة:"
    )
    await message.answer(welcome, reply_markup=main_menu())


# ========== Virtual Numbers ==========
@router.message(F.text == "📱 أرقام وهمية")
async def numbers_main(message: Message):
    balance = get_5sim_balance()
    balance_text = f"💰 رصيد 5sim: ${balance:.2f}" if balance else "💰 رصيد 5sim: —"
    await message.answer(
        f"📱 <b>خدمة الأرقام الوهمية</b>\n\n"
        f"{balance_text}\n\n"
        f"اختر الفئة المناسبة لك:",
        reply_markup=numbers_menu()
    )


@router.callback_query(F.data.startswith("num_tier"))
async def show_countries(callback: CallbackQuery):
    tier = callback.data.split("_")[1]
    tier_data = COUNTRIES[tier]
    await callback.message.edit_text(
        f"📱 <b>{tier_data['name']}</b>\n"
        f"💰 السعر: <b>${tier_data['price']}</b>\n\n"
        f"اختر الدولة:",
        reply_markup=countries_menu(tier)
    )


@router.callback_query(F.data.startswith("buy_"))
async def buy_number_handler(callback: CallbackQuery):
    parts = callback.data.split("_")
    country_code = parts[1]
    tier = parts[2]
    price = COUNTRIES[tier]["price"]
    country_name = COUNTRIES[tier]["countries"].get(country_code, country_code)

    await callback.message.edit_text("⏳ جاري شراء الرقم...")

    result = buy_number(country_code)

    if result["success"]:
        number_id = save_number(
            user_id=callback.from_user.id,
            order_id=str(result["id"]),
            phone=result["phone"],
            country_code=country_code,
            country_name=country_name,
            price=price
        )

        await callback.message.edit_text(
            f"✅ <b>تم شراء الرقم بنجاح!</b>\n\n"
            f"📱 الرقم: <code>{result['phone']}</code>\n"
            f"🌍 الدولة: {country_name}\n"
            f"💰 السعر: ${price}\n\n"
            f"⏳ سيصلك كود التفعيل خلال دقائق\n"
            f"اضغط 'استقبال الكود' للتحقق",
            reply_markup=number_actions_kb(number_id),
            parse_mode="HTML"
        )
    else:
        error_msg = result.get("error", "خطأ غير معروف")
        await callback.message.edit_text(
            f"❌ <b>فشل شراء الرقم</b>\n\n"
            f"السبب: {error_msg}\n\n"
            f"💡 تأكد من رصيد 5sim وحاول مرة أخرى"
        )


@router.callback_query(F.data.startswith("check_sms_"))
async def check_sms_handler(callback: CallbackQuery):
    number_id = int(callback.data.split("_")[2])
    number = get_active_number_by_order(str(callback.from_user.id))

    if not number:
        number = {"order_id": None}
        row = None
    else:
        row = number

    if not row or not row.get("order_id"):
        await callback.answer("❌ لم يتم العثور على الرقم", show_alert=True)
        return

    await callback.answer("⏳ جاري التحقق...")
    result = check_sms(row["order_id"])

    if result["success"]:
        code = result["code"]
        update_number_sms(number_id, code, result.get("text", ""))
        finish_order(int(row["order_id"]))
        await callback.message.edit_text(
            f"✅ <b>وصلك الكود!</b>\n\n"
            f"📱 الرقم: <code>{row['phone_number']}</code>\n"
            f"🔢 الكود: <code>{code}</code>",
            parse_mode="HTML"
        )
    else:
        await callback.answer(f"⏳ {result['error']}", show_alert=True)


@router.callback_query(F.data.startswith("cancel_num_"))
async def cancel_handler(callback: CallbackQuery):
    number_id = int(callback.data.split("_")[2])
    db_cancel_number(number_id)
    await callback.message.edit_text("✅ تم إلغاء الطلب واسترداد المبلغ.")


@router.callback_query(F.data == "my_numbers")
async def my_numbers_handler(callback: CallbackQuery):
    numbers = get_user_numbers(callback.from_user.id)
    if not numbers:
        await callback.message.edit_text(
            "📱 لا توجد أرقام مشتراة.\n\nاطلب رقم جديد من القائمة أعلاه ⬆️",
            reply_markup=numbers_menu()
        )
        return
    await callback.message.edit_text(
        "📱 <b>أرقامك المشتراة:</b>",
        reply_markup=my_numbers_kb(numbers)
    )


# ========== Boost Section ==========
@router.message(F.text == "👥 رشق وتفاعل")
async def boost_main(message: Message):
    points = get_points(message.from_user.id)
    await message.answer(
        f"👥 <b>قسم الرشق والتفاعل</b>\n\n"
        f"🎯 <b>نقاطك:</b> {points} نقطة\n\n"
        f"📌 <b>اكسب نقاط مجاناً:</b>\n"
        f"  ❤️ إعجاب = +1 نقطة\n"
        f"  📢 اشتراك قناة = +2 نقطة\n\n"
        f"📌 <b>استخدم نقاطك:</b>\n"
        f"  👥 رشق 1 متابع = 10 نقاط\n"
        f"  ❤️ رشق 1 إعجاب = 5 نقاط\n"
        f"  👁 رشق 1 مشاهدة = 3 نقاط",
        reply_markup=boost_menu()
    )


@router.callback_query(F.data == "earn_points")
async def earn_points_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        f"🎯 <b>اكسب نقاط مجاناً!</b>\n\n"
        f"اختر نوع المهمة:",
        reply_markup=earn_points_menu()
    )


@router.callback_query(F.data == "task_like")
async def task_like_start(callback: CallbackQuery, state: FSMContext):
    await state.update_data(task_type="like", points=1)
    await callback.message.edit_text(
        "📝 أرسل رابط المنشور الذي تريد الإعجاب به:\n\n"
        "مثال: https://t.me/channel/123456"
    )
    await state.set_state(States.waiting_link)


@router.callback_query(F.data == "task_subscribe")
async def task_subscribe_start(callback: CallbackQuery, state: FSMContext):
    await state.update_data(task_type="subscribe", points=2)
    await callback.message.edit_text(
        "📝 أرسل يوزر القناة (بدون @):\n\n"
        "مثال: king_bot_channel"
    )
    await state.set_state(States.waiting_link)


@router.message(States.waiting_link)
async def process_task_link(message: Message, state: FSMContext):
    data = await state.get_data()
    task_type = data["task_type"]
    points = data["points"]
    target = message.text.strip()

    create_task(message.from_user.id, task_type, target, points)
    await state.clear()
    await message.answer(
        f"✅ <b>تم تسجيل المهمة!</b>\n\n"
        f"📋 النوع: {task_type}\n"
        f"🎯 الهدف: {target}\n"
        f"🏆 المكافأة: {points} نقطة\n\n"
        f"⏳ سيتم المراجعة وإضافة النقاط قريباً"
    )


@router.callback_query(F.data == "boost_followers")
async def boost_followers_handler(callback: CallbackQuery, state: FSMContext):
    cost = 10
    if not deduct_points(callback.from_user.id, cost):
        await callback.answer("❌ نقاطك غير كافية! تحتاج 10 نقاط", show_alert=True)
        return
    await state.update_data(boost_type="followers")
    await callback.message.edit_text(
        f"👥 <b>رشق متابعين</b>\n"
        f"💰 التكلفة: 10 نقاط\n\n"
        f"أرسل يوزر القناة (بدون @):\n"
        f"مثال: my_channel"
    )
    await state.set_state(States.waiting_boost_target)


@router.callback_query(F.data == "boost_likes")
async def boost_likes_handler(callback: CallbackQuery, state: FSMContext):
    cost = 5
    if not deduct_points(callback.from_user.id, cost):
        await callback.answer("❌ نقاطك غير كافية! تحتاج 5 نقاط", show_alert=True)
        return
    await state.update_data(boost_type="likes")
    await callback.message.edit_text(
        f"❤️ <b>رشق إعجابات</b>\n"
        f"💰 التكلفة: 5 نقاط\n\n"
        f"أرسل رابط المنشور:\n"
        f"مثال: https://t.me/channel/123456"
    )
    await state.set_state(States.waiting_boost_target)


@router.callback_query(F.data == "boost_views")
async def boost_views_handler(callback: CallbackQuery, state: FSMContext):
    cost = 3
    if not deduct_points(callback.from_user.id, cost):
        await callback.answer("❌ نقاطك غير كافية! تحتاج 3 نقاط", show_alert=True)
        return
    await state.update_data(boost_type="views")
    await callback.message.edit_text(
        f"👁 <b>رشق مشاهدات</b>\n"
        f"💰 التكلفة: 3 نقاط\n\n"
        f"أرسل رابط المنشور:\n"
        f"مثال: https://t.me/channel/123456"
    )
    await state.set_state(States.waiting_boost_target)


@router.message(States.waiting_boost_target)
async def process_boost_target(message: Message, state: FSMContext):
    data = await state.get_data()
    boost_type = data["boost_type"]
    target = message.text.strip()

    boost_id = create_boost(message.from_user.id, boost_type, target, 1, 0)
    await state.clear()
    await message.answer(
        f"✅ <b>تم إنشاء طلب الرشق!</b>\n\n"
        f"📋 النوع: {boost_type}\n"
        f"🎯 الهدف: {target}\n"
        f"💰 التكلفة: {0} نقطة\n\n"
        f"⏳ جاري التنفيذ... سيصلك إشعار عند الانتهاء"
    )


# ========== Balance Section ==========
@router.message(F.text == "💰 شحن الرصيد")
async def balance_main(message: Message):
    balance = get_balance(message.from_user.id)
    await message.answer(
        f"💰 <b>قسم شحن الرصيد</b>\n\n"
        f"💳 <b>رصيدك الحالي:</b> ${balance:.2f}\n\n"
        f"طرق الشحن المتاحة:",
        reply_markup=balance_menu()
    )


@router.callback_query(F.data == "show_wallet")
async def show_wallet_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        f"💳 <b>عنوان المحفظة</b>\n\n"
        f"🪙 العملة: <b>{WALLET_COIN}</b>\n"
        f"🔗 الشبكة: <b>{WALLET_NETWORK}</b>\n\n"
        f"📋 العنوان:\n"
        f"<code>{WALLET_ADDRESS}</code>\n\n"
        f"⚠️ بعد الإرسال، اضغط 'تأكيد الدفع' وأرسل صورة الإثبات\n\n"
        f"💰 الحد الأدنى: $10",
        parse_mode="HTML"
    )


@router.callback_query(F.data == "confirm_deposit")
async def confirm_deposit_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "📸 أرسل صورة إثبات الدفع (Screenshot):\n\n"
        "أو أرسل هاش المعاملة (TxID)"
    )
    await state.set_state(States.waiting_deposit_amount)


@router.message(States.waiting_deposit_amount)
async def process_deposit(message: Message, state: FSMContext):
    user_id = message.from_user.id
    amount = 0.0
    tx_hash = ""

    if message.text:
        text = message.text.strip()
        # Try to parse amount or tx hash
        if text.startswith("http") or len(text) > 30:
            tx_hash = text
        else:
            try:
                amount = float(text.replace("$", ""))
            except ValueError:
                tx_hash = text

    from utils.database import create_order
    order_id = create_order(user_id, "deposit", amount, f"إيداع {'USDT'} - TX: {tx_hash or 'بانتظار'}")
    await state.clear()

    await message.answer(
        f"✅ <b>تم استلام طلب الإيداع!</b>\n\n"
        f"💰 المبلغ: ${amount if amount else 'بانتظار المراجعة'}\n"
        f"📋 رقم الطلب: #{order_id}\n\n"
        f"⏳ سيتم تأكيد الإيداع خلال 24 ساعة\n"
        f"💬 تواصل مع المطور لتسريع التأكيد"
    )


# ========== Profile ==========
@router.message(F.text == "� حسابي")
async def profile_handler(message: Message):
    try:
        user_id = message.from_user.id
        register_user(user_id, message.from_user.username or "", message.from_user.full_name or "")
        from utils.database import get_user
        user_data = get_user(user_id)
        if user_data:
            points = user_data.get("points", 0)
            balance = user_data.get("balance", 0.0)
        else:
            points = 0
            balance = 0.0

        await message.answer(
            f"📊 <b>ملفك الشخصي</b>\n\n"
            f"� الا�م: {message.from_user.full_name or '—'}\n"
            f"� ID: <code>{user_id}</code>\n"
            f"� النقاط: {points} نقطة\n"
            f"💰 الرصيد: ${balance:.2f}",
            parse_mode="HTML"
        )
    except Exception as e:
        await message.answer(
            "� معلومات الحساب:\n\n"
            "💰 الرصيد الحالي: $0.00\n"
            "🚀 النقاط الحالية: 0\n"
            "🆔 المعرف الخاص بك: المالك"
        )


# ========== Contact ==========
@router.message(F.text == "📞 تواصل مع المطور")
async def contact_handler(message: Message):
    await message.answer(
        f"📞 <b>تواصل مع المطور:</b>\n\n"
        f"💬 {DEVELOPER_USERNAME}\n\n"
        f"❓ لأي استفسار أو مشكلة، راسلني مباشرة."
    )


# ========== Channel Button ==========
@router.message(F.text == "📢 قناة البوت")
async def channel_handler(message: Message):
    await message.answer(
        f"📢 <b>قناة البوت الرسمية:</b>\n\n"
        f"@king_bot_channel\n\n"
        f"📌 هنا آخر التحديثات والأخبار"
    )


# ========== Back Navigation ==========
@router.callback_query(F.data == "back_main")
async def back_main(callback: CallbackQuery):
    points = get_points(callback.from_user.id)
    balance = get_balance(callback.from_user.id)
    await callback.message.edit_text(
        f"🏠 <b>القائمة الرئيسية</b>\n\n"
        f"🎯 نقاطك: {points} ⬿ 💰 رصيدك: ${balance:.2f}\n\n"
        f"اختر من القائمة ⬇️",
        reply_markup=main_menu()
    )


@router.callback_query(F.data == "back_numbers")
async def back_numbers(callback: CallbackQuery):
    await callback.message.edit_text(
        f"📱 <b>خدمة الأرقام الوهمية</b>\n\nاختر الفئة:",
        reply_markup=numbers_menu()
    )


@router.callback_query(F.data == "back_boost")
async def back_boost(callback: CallbackQuery):
    points = get_points(callback.from_user.id)
    await callback.message.edit_text(
        f"👥 <b>قسم الرشق والتفاعل</b>\n\n"
        f"🎯 نقاطك: {points} نقطة",
        reply_markup=boost_menu()
    )
