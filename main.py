import asyncio
import json
from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.enums import ParseMode
from aiogram.filters import Command, StateFilter, CommandObject
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

API_TOKEN = "7754616976:AAEY9iDvx1230-6C7LUQuwSum_HqEQfpxJ0"
ADMIN_ID = 5989586412  # ← غيّره لـ ID حسابك
orders_file = "orders.json"
affiliates_file = "affiliates.json"
preview_target = {}

bot = Bot(token=API_TOKEN,
          default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

main_menu = ReplyKeyboardMarkup(
    resize_keyboard=True,
    keyboard=[[
        types.KeyboardButton(text="🖌️ اطلب تصميم"),
        types.KeyboardButton(text="💵 الأسعار")
    ],
              [
                  types.KeyboardButton(text="🖼️ معرض الأعمال"),
                  types.KeyboardButton(text="📞 تواصل معنا")
              ], [types.KeyboardButton(text="🎯 الإحالة")]])

affiliate_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🔗 رابط الإحالة", callback_data="ref_link")],
    [InlineKeyboardButton(text="👥 عدد الإحالات", callback_data="ref_count")],
    [InlineKeyboardButton(text="💰 رصيدي", callback_data="ref_balance")],
    [InlineKeyboardButton(text="💸 سحب الأرباح", callback_data="ref_withdraw")]
])

payment_methods = InlineKeyboardMarkup(inline_keyboard=[[
    InlineKeyboardButton(text="📱 فودافون كاش", callback_data="pay_vodafone")
], [
    InlineKeyboardButton(text="📱 اتصالات كاش", callback_data="pay_etisalat")
], [InlineKeyboardButton(text="💰 USDT (TRC20)", callback_data="pay_usdt")]])


class Order(StatesGroup):
    design_type = State()
    custom_type = State()
    text = State()
    idea = State()
    colors = State()


class Withdraw(StatesGroup):
    waiting_for_method = State()
    waiting_for_number = State()


class Rejection(StatesGroup):
    waiting_for_reason = State()


class Revision(StatesGroup):
    waiting_for_revisions = State()


def load_affiliates():
    try:
        with open(affiliates_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def save_affiliates(data):
    with open(affiliates_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


@router.message(Command("start"))
async def start(message: types.Message, state: FSMContext,
                command: CommandObject):
    affiliates = load_affiliates()
    user_id = str(message.from_user.id)
    referrer_id = None

    if command.args and command.args.startswith("ref_"):
        referrer_id = command.args.split("ref_")[1]
        if user_id not in affiliates and referrer_id != user_id:
            affiliates[user_id] = {
                "ref": referrer_id,
                "joined": True,
                "orders": 0,
                "balance": 0
            }
            save_affiliates(affiliates)

    if user_id not in affiliates:
        affiliates[user_id] = {
            "ref": None,
            "joined": True,
            "orders": 0,
            "balance": 0
        }
        save_affiliates(affiliates)

    await message.answer(
        "مرحبًا بك في بوت التصميم الخاص بـ <b>مسلم أبوشنب</b> 🎨",
        reply_markup=main_menu)


@router.message(F.text == "🖌️ اطلب تصميم")
async def ask_type(message: types.Message, state: FSMContext):
    buttons = [[
        InlineKeyboardButton(text="🎬 مصغرة يوتيوب - 75ج",
                             callback_data="type_youtube")
    ],
               [
                   InlineKeyboardButton(text="📱 بوست سوشيال - 50ج",
                                        callback_data="type_social")
               ],
               [
                   InlineKeyboardButton(text="🎨 لوجو - 75ج",
                                        callback_data="type_logo")
               ],
               [
                   InlineKeyboardButton(text="🧩 تصميم خاص",
                                        callback_data="type_custom")
               ]]
    await message.answer(
        "📌 اختر نوع التصميم:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


@router.callback_query(F.data.startswith("type_"))
async def handle_type(call: types.CallbackQuery, state: FSMContext):
    t = call.data.split("_")[1]
    await state.update_data(design_type=t)

    if t == "custom":
        await state.set_state(Order.custom_type)
        await call.message.answer("✍️ ما نوع التصميم الخاص المطلوب؟")
    else:
        await state.set_state(Order.text)
        await call.message.answer("📝 ما النص الذي تريد كتابته؟")


@router.message(StateFilter(Order.custom_type))
async def get_custom_type(message: types.Message, state: FSMContext):
    await state.update_data(custom_type=message.text)
    await state.set_state(Order.text)
    await message.answer("📝 ما النص الذي تريد كتابته؟")


@router.message(StateFilter(Order.text))
async def get_text(message: types.Message, state: FSMContext):
    await state.update_data(text=message.text)
    await state.set_state(Order.idea)
    await message.answer("💡 هل لديك فكرة معينة للتصميم؟")


@router.message(StateFilter(Order.idea))
async def get_idea(message: types.Message, state: FSMContext):
    await state.update_data(idea=message.text)
    await state.set_state(Order.colors)
    await message.answer("🎨 ما الألوان المفضلة؟")


@router.message(StateFilter(Order.colors))
async def get_colors(message: types.Message, state: FSMContext):
    await state.update_data(colors=message.text)
    data = await state.get_data()
    type_display = {
        "youtube": "مصغرة يوتيوب - 75ج",
        "social": "بوست سوشيال - 50ج",
        "logo": "لوجو - 75ج",
        "custom": f"تصميم خاص - {data.get('custom_type')} (السعر حسب الطلب)"
    }

    await bot.send_message(
        ADMIN_ID, f"🔔 طلب تصميم جديد:\n"
        f"👤 المستخدم: @{message.from_user.username or 'بدون يوزر'}\n"
        f"🆔 ID: <code>{message.from_user.id}</code>\n"
        f"📌 النوع: {type_display[data['design_type']]}\n"
        f"💬 النص: {data['text']}\n"
        f"💡 الفكرة: {data['idea']}\n"
        f"🎨 الألوان: {data['colors']}")
    await message.answer(
        "✅ شكرًا! سيتم إرسال معاينة التصميم قريبًا حسب المواصفات.")
    await state.clear()


@router.message(Command("preview"))
async def send_preview(message: types.Message, command: CommandObject):
    if message.from_user.id != ADMIN_ID:
        return
    if not command.args:
        await message.answer("❗ استخدم الأمر كالتالي:\n/preview USER_ID")
        return
    try:
        target_id = int(command.args.strip())
        await bot.send_message(target_id, "📸 هذه معاينة التصميم الخاصة بك:")
        preview_target[target_id] = True
        await message.answer("✅ أرسل الآن صورة المعاينة للعميل.")
    except:
        await message.answer("❌ لم يتم التعرف على ID.")


@router.message(F.photo)
async def handle_preview_photo(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    for uid in preview_target:
        if preview_target[uid]:
            await bot.send_photo(
                uid,
                message.photo[-1].file_id,
                caption="✅ هذه معاينة التصميم، هل ترغب بالاستمرار؟",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(text="✅ نعم",
                                             callback_data="continue_design")
                    ],
                    [
                        InlineKeyboardButton(text="✏️ أريد بعض التعديلات",
                                             callback_data="ask_revision")
                    ],
                    [
                        InlineKeyboardButton(text="❌ لا",
                                             callback_data="reject_design")
                    ]
                ]))
            preview_target[uid] = False


@router.callback_query(F.data == "continue_design")
async def confirm_payment(call: types.CallbackQuery):
    await call.message.answer("💵 من فضلك اختر وسيلة الدفع:",
                              reply_markup=payment_methods)


@router.callback_query(F.data.startswith("pay_"))
async def send_payment_details(call: types.CallbackQuery):
    method = call.data.split("_")[1]
    if method == "vodafone":
        msg = "🔻 فودافون كاش:\n01033410783"
    elif method == "etisalat":
        msg = "🔻 اتصالات كاش:\n01146087295"
    elif method == "usdt":
        msg = "🔻 USDT TRC20:\nTQRidCAEEnLLH3WvdozCaGa1sFQ7a2fkQF"
    else:
        msg = "❗ طريقة غير معروفة"

    msg += "\n\n📸 بعد التحويل، من فضلك أرسل سكرين شوت للإثبات هنا."
    await call.message.answer(msg)


@router.message(F.photo)
async def receive_payment_proof(message: types.Message):
    await bot.send_photo(
        ADMIN_ID,
        message.photo[-1].file_id,
        caption=
        f"🧾 إثبات دفع من: @{message.from_user.username or 'بدون يوزر'}\n🆔 {message.from_user.id}"
    )


@router.callback_query(F.data == "ask_revision")
async def ask_revision_text(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(Revision.waiting_for_revisions)
    await call.message.answer("✏️ ما التعديلات التي ترغب بها؟")


@router.message(StateFilter(Revision.waiting_for_revisions))
async def send_revision_to_admin(message: types.Message, state: FSMContext):
    await bot.send_message(
        ADMIN_ID,
        f"🔄 طلب تعديل من @{message.from_user.username or 'بدون يوزر'}:\n{message.text}"
    )
    await message.answer("✅ تم إرسال طلب التعديلات. سيتم تنفيذها قريبًا.")
    await state.clear()


@router.callback_query(F.data == "reject_design")
async def ask_reject_reason(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(Rejection.waiting_for_reason)
    await call.message.answer("😔 يُرجى إخبارنا بسبب رفض التصميم.")


@router.message(StateFilter(Rejection.waiting_for_reason))
async def handle_rejection(message: types.Message, state: FSMContext):
    await bot.send_message(
        ADMIN_ID,
        f"❌ سبب رفض الطلب من @{message.from_user.username or 'بدون يوزر'}:\n{message.text}"
    )
    await message.answer(
        "🙏 شكرًا على استخدامك للبوت. نأمل أن نخدمك بشكل أفضل لاحقًا.")
    await state.clear()


@router.message(F.text == "💵 الأسعار")
async def show_prices(message: types.Message):
    await message.answer(
        "💵 الأسعار:\n🎬 مصغرة يوتيوب: 75ج\n📱 بوست سوشيال: 50ج\n🎨 لوجو: 75ج\n🧩 تصميم خاص: حسب الطلب"
    )


@router.message(F.text == "📞 تواصل معنا")
async def contact_info(message: types.Message):
    await message.answer("📞 للتواصل مع المصمم:\n@Muslimshaban")


@router.message(F.text == "🖼️ معرض الأعمال")
async def gallery(message: types.Message):
    await message.answer("المعرض تحت التطوير، يرجى المحاولة لاحقًا.")


@router.message(F.text == "🎯 الإحالة")
async def referral_menu(message: types.Message):
    await message.answer("🎯 مرحبًا بك في نظام الإحالة!",
                         reply_markup=affiliate_menu)


@router.callback_query(F.data == "ref_link")
async def ref_link(call: types.CallbackQuery):
    user_id = call.from_user.id
    link = f"https://t.me/@fastdesign1907_bot?start=ref_{user_id}"
    await call.message.answer(f"🔗 رابط الإحالة الخاص بك:\n{link}")


@router.callback_query(F.data == "ref_count")
async def ref_count(call: types.CallbackQuery):
    user_id = str(call.from_user.id)
    affiliates = load_affiliates()
    count = sum(1 for v in affiliates.values() if v.get("ref") == user_id)
    await call.message.answer(f"👥 عدد الإحالات: {count}")


@router.callback_query(F.data == "ref_balance")
async def ref_balance(call: types.CallbackQuery):
    user_id = str(call.from_user.id)
    affiliates = load_affiliates()
    balance = affiliates.get(user_id, {}).get("balance", 0)
    await call.message.answer(f"💰 رصيدك الحالي: {balance} جنيه")


@router.callback_query(F.data == "ref_withdraw")
async def ref_withdraw(call: types.CallbackQuery, state: FSMContext):
    user_id = str(call.from_user.id)
    affiliates = load_affiliates()
    balance = affiliates.get(user_id, {}).get("balance", 0)
    if balance < 10:
        await call.message.answer("❗ لا يمكن السحب قبل الوصول إلى 10 جنيه.")
    else:
        await state.set_state(Withdraw.waiting_for_method)
        await call.message.answer(
            "💸 اختر وسيلة السحب:\n- فودافون كاش\n- اتصالات كاش")


@router.message(StateFilter(Withdraw.waiting_for_method))
async def get_withdraw_method(message: types.Message, state: FSMContext):
    method = message.text
    if method not in ["فودافون كاش", "اتصالات كاش"]:
        return await message.answer("❗ من فضلك اختر وسيلة صحيحة.")
    await state.update_data(method=method)
    await state.set_state(Withdraw.waiting_for_number)
    await message.answer("📱 من فضلك أرسل رقم الهاتف لاستلام المبلغ.")


@router.message(StateFilter(Withdraw.waiting_for_number))
async def confirm_withdraw(message: types.Message, state: FSMContext):
    number = message.text
    data = await state.get_data()
    method = data["method"]
    user_id = str(message.from_user.id)
    affiliates = load_affiliates()
    amount = affiliates.get(user_id, {}).get("balance", 0)

    if amount < 10:
        await message.answer("❗ رصيدك لا يكفي.")
        return await state.clear()

    affiliates[user_id]["balance"] = 0
    save_affiliates(affiliates)

    await bot.send_message(
        ADMIN_ID,
        f"🔔 طلب سحب جديد:\n👤 المستخدم: @{message.from_user.username}\n📱 رقم: {number}\n💳 الوسيلة: {method}\n💰 المبلغ: {amount}ج"
    )
    await message.answer(
        "✅ تم إرسال طلب السحب. سيتم المراجعة والإرسال خلال وقت قصير.")
    await state.clear()


# تشغيل البوت
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    from keep_alive import keep_alive
    keep_alive()
    asyncio.run(main())

