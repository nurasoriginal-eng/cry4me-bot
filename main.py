import asyncio
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from config import (
    BOT_TOKEN, ADMIN_IDS, PRODUCTS,
    KASPI_NUMBER, CRYPTO_WALLET, SUPPORT_URL
)
import database as db

# ---- Render үшін веб-сервер параметрлері ----
WEBHOOK_HOST = os.getenv("RENDER_EXTERNAL_URL", "https://your-app.onrender.com")
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
WEB_SERVER_HOST = "0.0.0.0"
WEB_SERVER_PORT = int(os.getenv("PORT", 10000))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

class BuyState(StatesGroup):
    waiting_receipt = State()

class AdminState(StatesGroup):
    waiting_keys = State()

# ---------- КЛАВИАТУРАЛАР ----------
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 CRY4ME сатып алу", callback_data="prod:cry4me")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton(text="💬 Қолдау", url=SUPPORT_URL)],
    ])

def plans_menu(pid):
    p = PRODUCTS[pid]
    kb = []
    for plan_id, plan in p["plans"].items():
        kb.append([InlineKeyboardButton(
            text=f"{plan['label']} — {plan['price']}₸",
            callback_data=f"buy:{pid}:{plan_id}"
        )])
    kb.append([InlineKeyboardButton(text="⬅️ Артқа", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def confirm_menu(pid, plan_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Төледім", callback_data=f"paid:{pid}:{plan_id}")],
        [InlineKeyboardButton(text="⬅️ Артқа", callback_data=f"prod:{pid}")],
    ])

def admin_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Тапсырыстар", callback_data="admin:orders")],
        [InlineKeyboardButton(text="📦 Қойма", callback_data="admin:stock")],
        [InlineKeyboardButton(text="➕ Ключ қосу", callback_data="admin:addkeys")],
    ])

def back_to_admin():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Артқа", callback_data="admin:menu")]
    ])

# ---------- ПАЙДАЛАНУШЫ ----------
@dp.message(CommandStart())
async def start(msg: Message):
    await msg.answer(
        f"Сәлем, {msg.from_user.full_name}!\n\n"
        "🔥 <b>CRY4ME</b> дүкеніне қош келдің!",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "back")
async def back(cb: CallbackQuery):
    await cb.message.edit_text("Басты мәзір:", reply_markup=main_menu())
    await cb.answer()

@dp.callback_query(F.data.startswith("prod:"))
async def show_plans(cb: CallbackQuery):
    pid = cb.data.split(":")[1]
    p = PRODUCTS[pid]
    text = (
        f"🔥 <b>{p['name']}</b>\n\n"
        f"<b>Бағалар:</b>\n"
        f"• 1 DAY — 2000₸\n"
        f"• 1 WEEK — 4500₸\n"
        f"• 1 MONTH — 15000₸\n\n"
        f"Тарифті таңда:"
    )
    await cb.message.edit_text(text, reply_markup=plans_menu(pid), parse_mode="HTML")
    await cb.answer()

@dp.callback_query(F.data.startswith("buy:"))
async def buy(cb: CallbackQuery):
    _, pid, plan_id = cb.data.split(":")
    p = PRODUCTS[pid]
    plan = p["plans"][plan_id]
    stock = await db.count_stock(pid, plan_id)

    if stock == 0:
        await cb.answer("❌ Қоймада жоқ!", show_alert=True)
        return

    text = (
        f"🛒 <b>{p['name']}</b>\n"
        f"📅 Тариф: <b>{plan['label']}</b>\n"
        f"💰 Бағасы: <b>{plan['price']}₸</b>\n"
        f"📦 Қоймада: {stock} дана\n\n"
        f"<b>Төлем:</b>\n"
        f"Kaspi: <code>{KASPI_NUMBER}</code>\n"
        f"USDT: <code>{CRYPTO_WALLET}</code>\n\n"
        f"Төлеп, чекті осы чатқа жібер 👇"
    )
    await cb.message.edit_text(text, reply_markup=confirm_menu(pid, plan_id), parse_mode="HTML")
    await cb.answer()

@dp.callback_query(F.data.startswith("paid:"))
async def paid(cb: CallbackQuery, state: FSMContext):
    _, pid, plan_id = cb.data.split(":")
    await state.update_data(pid=pid, plan_id=plan_id)
    await state.set_state(BuyState.waiting_receipt)
    await cb.message.answer("📸 Чекті жібер:")
    await cb.answer()

@dp.message(BuyState.waiting_receipt, F.photo)
async def receipt(msg: Message, state: FSMContext):
    data = await state.get_data()
    pid, plan_id = data["pid"], data["plan_id"]
    p = PRODUCTS[pid]
    plan = p["plans"][plan_id]

    for admin in ADMIN_IDS:
        await bot.send_photo(
            admin,
            msg.photo[-1].file_id,
            caption=(
                f"🆕 <b>Жаңа тапсырыс!</b>\n\n"
                f"👤 @{msg.from_user.username} (ID: <code>{msg.from_user.id}</code>)\n"
                f"📦 {p['name']} — {plan['label']}\n"
                f"💰 {plan['price']}₸"
            ),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(
                    text="✅ Растау",
                    callback_data=f"admin:approve:{msg.from_user.id}:{pid}:{plan_id}"
                ),
                InlineKeyboardButton(
                    text="❌ Қабылдамау",
                    callback_data=f"admin:reject:{msg.from_user.id}"
                ),
            ]])
        )
    await msg.answer("✅ Чек қабылданды! Админ тексереді.")
    await state.clear()

@dp.message(BuyState.waiting_receipt)
async def receipt_wrong(msg: Message):
    await msg.answer("❗ Сурет жібер.")

# ---------- АДМИН ----------
@dp.message(Command("admin"))
async def admin_cmd(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        return
    await msg.answer("🔧 <b>Админ панель</b>", reply_markup=admin_menu(), parse_mode="HTML")

@dp.callback_query(F.data == "admin:menu")
async def admin_menu_cb(cb: CallbackQuery):
    if cb.from_user.id not in ADMIN_IDS:
        return
    await cb.message.edit_text("🔧 <b>Админ панель</b>", reply_markup=admin_menu(), parse_mode="HTML")
    await cb.answer()

@dp.callback_query(F.data == "admin:orders")
async def admin_orders(cb: CallbackQuery):
    if cb.from_user.id not in ADMIN_IDS:
        return
    orders = await db.get_all_orders()
    text = "📋 <b>Тапсырыстар:</b>\n\n"
    if not orders:
        text = "📋 Тапсырыстар жоқ."
    else:
        for oid, uid, prod, plan, key, date in orders:
            text += f"#{oid} | <code>{uid}</code> | {key or 'жоқ'}\n"
    await cb.message.edit_text(text, reply_markup=back_to_admin(), parse_mode="HTML")
    await cb.answer()

@dp.callback_query(F.data == "admin:stock")
async def admin_stock(cb: CallbackQuery):
    if cb.from_user.id not in ADMIN_IDS:
        return
    text = "📦 <b>Қойма:</b>\n\n"
    for pid, p in PRODUCTS.items():
        text += f"🔥 <b>{p['name']}</b>\n"
        for plan_id, plan in p["plans"].items():
            c = await db.count_stock(pid, plan_id)
            text += f"  • {plan['label']}: {c} дана\n"
    await cb.message.edit_text(text, reply_markup=back_to_admin(), parse_mode="HTML")
    await cb.answer()

@dp.callback_query(F.data == "admin:addkeys")
async def admin_addkeys(cb: CallbackQuery, state: FSMContext):
    if cb.from_user.id not in ADMIN_IDS:
        return
    await state.set_state(AdminState.waiting_keys)
    await cb.message.edit_text(
        "➕ <b>Ключ қосу</b>\n\n"
        "Формат: <code>cry4me 1day KEY-1, KEY-2</code>",
        reply_markup=back_to_admin(),
        parse_mode="HTML"
    )
    await cb.answer()

@dp.message(AdminState.waiting_keys)
async def process_addkeys(msg: Message, state: FSMContext):
    if msg.from_user.id not in ADMIN_IDS:
        return
    try:
        parts = msg.text.split(maxsplit=2)
        pid, plan_id, keys_str = parts[0], parts[1], parts[2]
        keys = [k.strip() for k in keys_str.split(",") if k.strip()]
        if pid not in PRODUCTS or plan_id not in PRODUCTS[pid]["plans"]:
            await msg.answer("❌ Қате формат.")
            return
        await db.add_keys(pid, plan_id, keys)
        await msg.answer(f"✅ {len(keys)} ключ қосылды!")
    except Exception as e:
        await msg.answer(f"❌ Қате: {e}")
    await state.clear()

@dp.callback_query(F.data.startswith("admin:approve:"))
async def admin_approve(cb: CallbackQuery):
    if cb.from_user.id not in ADMIN_IDS:
        return
    _, _, uid, pid, plan_id = cb.data.split(":")
    uid = int(uid)
    key = await db.get_key(pid, plan_id)
    if not key:
        await cb.answer("❌ Қоймада жоқ!", show_alert=True)
        return
    await db.save_purchase(uid, pid, plan_id, key)
    plan = PRODUCTS[pid]["plans"][plan_id]
    try:
        await bot.send_message(
            uid,
            f"🎉 <b>Расталды!</b>\n\n"
            f"🔥 {PRODUCTS[pid]['name']}\n"
            f"📅 {plan['label']}\n"
            f"🔑 <code>{key}</code>",
            parse_mode="HTML"
        )
    except:
        pass
    await cb.message.edit_caption(
        caption=f"✅ Расталды. Ключ: <code>{key}</code>",
        parse_mode="HTML"
    )
    await cb.answer("✅")

@dp.callback_query(F.data.startswith("admin:reject:"))
async def admin_reject(cb: CallbackQuery):
    if cb.from_user.id not in ADMIN_IDS:
        return
    _, _, uid = cb.data.split(":")
    uid = int(uid)
    try:
        await bot.send_message(uid, "❌ Төлем расталмады.")
    except:
        pass
    await cb.message.edit_caption(caption="❌ Қабылданбады")
    await cb.answer("❌")

@dp.callback_query(F.data == "profile")
async def profile(cb: CallbackQuery):
    rows = await db.user_purchases(cb.from_user.id)
    if not rows:
        text = "👤 Сатып алулар жоқ."
    else:
        text = "👤 <b>Сенің сатып алуларың:</b>\n\n"
        for product, plan, key, date in rows:
            text += f"🔑 <code>{key}</code>\n📅 {date}\n\n"
    await cb.message.edit_text(text, parse_mode="HTML", reply_markup=main_menu())
    await cb.answer()

# ---------- WEBHOOK ----------
async def on_startup(bot: Bot):
    await db.init_db()
    await bot.set_webhook(WEBHOOK_URL)
    print(f"Webhook set to {WEBHOOK_URL}")

async def on_shutdown(bot: Bot):
    await bot.delete_webhook()

def main():
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    app = web.Application()
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    # Health check үшін
    async def health(request):
        return web.Response(text="OK")

    app.router.add_get("/", health)

    web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)

if __name__ == "__main__":
    main()
