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
    KASPI_NUMBER, CRYPTO_WALLET, SUPPORT_URL,
    MAIN_PHOTO, ANDROID_PHOTO
)
import database as db

# ---- КАНАЛ ID (Отзывтар баратын жер) ----
REVIEW_CHANNEL_ID = -1004492854668

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

class ReviewState(StatesGroup):
    waiting_text = State()

# ---------- КЛАВИАТУРАЛАР ----------
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Чит сатып алу", callback_data="choose_platform")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton(text="💬 Қолдау", url=SUPPORT_URL)],
    ])

def platform_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 ANDROID NROOT (БЕЗ РУТ)", callback_data="plat:android")],
        [InlineKeyboardButton(text="🍏 IOS", callback_data="plat:ios")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back")],
    ])

def android_products_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ MAGIC VIP", callback_data="prod:android_magic_vip")],
        [InlineKeyboardButton(text="💎 MAGIC LITE", callback_data="prod:android_magic_lite")],
        [InlineKeyboardButton(text="☠️ CRY4ME", callback_data="prod:android_cry4me")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="choose_platform")],
    ])

def ios_products_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="☠️ AQREH", callback_data="prod:ios_aqreh")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="choose_platform")],
    ])

def plans_menu(pid, stock_counts=None):
    p = PRODUCTS[pid]
    kb = []
    for plan_id, plan in p["plans"].items():
        stock_text = f" | {stock_counts[plan_id]} шт." if stock_counts else ""
        currency = "₸" 
        kb.append([InlineKeyboardButton(
            text=f"{plan['label']} | {plan['price']} {currency}{stock_text}",
            callback_data=f"buy:{pid}:{plan_id}"
        )])
    back_data = "plat:android" if p["platform"] == "android" else "plat:ios"
    kb.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=back_data)])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def confirm_menu(pid, plan_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Я оплатил", callback_data=f"paid:{pid}:{plan_id}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"prod:{pid}")],
    ])

def review_stars_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐", callback_data="rate:1"),
         InlineKeyboardButton(text="⭐⭐", callback_data="rate:2"),
         InlineKeyboardButton(text="⭐⭐⭐", callback_data="rate:3")],
        [InlineKeyboardButton(text="⭐⭐⭐⭐", callback_data="rate:4"),
         InlineKeyboardButton(text="⭐⭐⭐⭐⭐", callback_data="rate:5")],
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
        "🔥 <b>Читтер дүкеніне қош келдің!</b>\n"
        "Сатып алу үшін төмендегі батырманы бас.",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )

# ОРТАҚ ФУНКЦИЯ: Ескі хабарламаны өшіріп, жаңа суретті хабарлама жіберу
async def send_new_photo_msg(cb: CallbackQuery, photo: str, text: str, menu: InlineKeyboardMarkup):
    await cb.message.delete()
    await cb.message.answer_photo(
        photo=photo, 
        caption=text, 
        reply_markup=menu, 
        parse_mode="HTML"
    )

# ОРТАҚ ФУНКЦИЯ: Ескі хабарламаны өшіріп, жаңа мәтіндік хабарлама жіберу
async def send_new_text_msg(cb: CallbackQuery, text: str, menu: InlineKeyboardMarkup = None):
    await cb.message.delete()
    await cb.message.answer(text, reply_markup=menu, parse_mode="HTML")


@dp.callback_query(F.data == "back")
async def back(cb: CallbackQuery):
    await send_new_text_msg(cb, "Басты мәзір:", main_menu())
    await cb.answer()

@dp.callback_query(F.data == "choose_platform")
async def choose_platform(cb: CallbackQuery):
    text = (
        "<b>PRIVATE SOFT</b>\n"
        "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        "🛡 Надежные приватные решения.\n"
        "🛡 Мы тщательно следим за каждым обновлением.\n"
        "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        "📱 <b>Выберите ваше устройство</b>"
    )
    await send_new_photo_msg(cb, MAIN_PHOTO, text, platform_menu())
    await cb.answer()

@dp.callback_query(F.data.startswith("plat:"))
async def choose_product(cb: CallbackQuery):
    plat = cb.data.split(":")[1]
    
    if plat == "android":
        text = (
            "🤖 <b>ANDROID NROOT (БЕЗ РУТ)</b>\n"
            "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
            "🔥 Софт который не требует ROOT прав\n\n"
            "❗️ Если вы не знаете что такое ROOT права, то скорее всего у вас их нет и данная категория для вас подходит.\n"
            "❗️ Ознакомьтесь с софтами, у каждого разный функционал и внешний вид."
        )
        await send_new_photo_msg(cb, ANDROID_PHOTO, text, android_products_menu())
    else:
        text = (
            "🍏 <b>IOS (iPhone)</b>\n"
            "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
            "🔥 Приватные решения для iOS.\n\n"
            "Выберите нужный софт:"
        )
        await send_new_photo_msg(cb, MAIN_PHOTO, text, ios_products_menu())
    
    await cb.answer()

@dp.callback_query(F.data.startswith("prod:"))
async def show_plans(cb: CallbackQuery):
    pid = cb.data.split(":")[1]
    p = PRODUCTS[pid]
    
    if p.get("in_dev"):
        await cb.answer("🚧 Бұл чит әзірленуде (В разработке)! Жақын арада қосылады.", show_alert=True)
        return
    
    stock_counts = {}
    for plan_id in p["plans"].keys():
        count = await db.count_stock(pid, plan_id)
        stock_counts[plan_id] = count

    text = f"<b>{p['name']}</b>\n"
    if "description" in p:
        text += f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n{p['description']}\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯"
    
    await send_new_photo_msg(cb, p["photo"], text, plans_menu(pid, stock_counts))
    await cb.answer()

@dp.callback_query(F.data.startswith("buy:"))
async def buy(cb: CallbackQuery):
    _, pid, plan_id = cb.data.split(":")
    p = PRODUCTS[pid]
    plan = p["plans"][plan_id]
    stock = await db.count_stock(pid, plan_id)

    if stock == 0:
        await cb.answer("❌ Бұл тариф қоймада жоқ!", show_alert=True)
        return

    text = (
        f"🛒 <b>{p['name']}</b>\n"
        f"📅 Тариф: <b>{plan['label']}</b>\n"
        f"💰 Бағасы: <b>{plan['price']}₸</b>\n"
        f"📦 Қоймада: {stock} дана\n\n"
        f"<b>Төлем әдістері:</b>\n"
        f"1️⃣ Kaspi: <code>{KASPI_NUMBER}</code>\n"
        f"2️⃣ USDT (TRC20): <code>{CRYPTO_WALLET}</code>\n\n"
        f"Төлеген соң чектің скриншотын осы чатқа жібер 👇"
    )
    
    await send_new_text_msg(cb, text, confirm_menu(pid, plan_id))
    await cb.answer()

@dp.callback_query(F.data.startswith("paid:"))
async def paid(cb: CallbackQuery, state: FSMContext):
    _, pid, plan_id = cb.data.split(":")
    await state.update_data(pid=pid, plan_id=plan_id)
    await state.set_state(BuyState.waiting_receipt)
    await cb.message.answer("📸 Чекті жібер:")
    await cb.answer()

@dp.message(BuyState.waiting_receipt, F.photo | F.document)
async def receipt(msg: Message, state: FSMContext):
    data = await state.get_data()
    pid, plan_id = data["pid"], data["plan_id"]
    p = PRODUCTS[pid]
    plan = p["plans"][plan_id]

    caption = (
        f"🆕 <b>Жаңа тапсырыс!</b>\n\n"
        f"👤 @{msg.from_user.username} (ID: <code>{msg.from_user.id}</code>)\n"
        f"📦 {p['name']} — {plan['label']}\n"
        f"💰 {plan['price']}₸"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="✅ Растау",
            callback_data=f"admin:approve:{msg.from_user.id}:{pid}:{plan_id}"
        ),
        InlineKeyboardButton(
            text="❌ Қабылдамау",
            callback_data=f"admin:reject:{msg.from_user.id}"
        ),
    ]])

    for admin in ADMIN_IDS:
        if msg.photo:
            await bot.send_photo(admin, msg.photo[-1].file_id, caption=caption, parse_mode="HTML", reply_markup=keyboard)
        elif msg.document:
            await bot.send_document(admin, msg.document.file_id, caption=caption, parse_mode="HTML", reply_markup=keyboard)

    await msg.answer("✅ Чек қабылданды! Админ тексереді.")
    await state.clear()

@dp.message(BuyState.waiting_receipt)
async def receipt_wrong(msg: Message):
    await msg.answer("❗ Сурет немесе PDF жібер.")

# ---------- ОТЗЫВ (ПІКІР) ЖҮЙЕСІ ----------
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
        
        await asyncio.sleep(2)
        await bot.send_message(
            uid,
            "⭐️ <b>Сатып алуыңыз сәтті өтті!</b>\n\n"
            "Бізге пікір қалдырыңыз. Қызметімізді 5 жұлдызбен бағалаңыз:",
            reply_markup=review_stars_menu(),
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

@dp.callback_query(F.data.startswith("rate:"))
async def process_rating(cb: CallbackQuery, state: FSMContext):
    rating = int(cb.data.split(":")[1])
    await state.update_data(rating=rating)
    await state.set_state(ReviewState.waiting_text)
    
    stars = "⭐" * rating
    await cb.message.edit_text(
        f"Сіз {stars} бағасын таңдадыңыз.\n\n"
        f"Енді пікіріңізді жазыңыз (қазақша немесе орысша):"
    )
    await cb.answer()

@dp.message(ReviewState.waiting_text)
async def process_review_text(msg: Message, state: FSMContext):
    data = await state.get_data()
    rating = data["rating"]
    text = msg.text
    
    await db.save_review(msg.from_user.id, rating, text)
    
    await msg.answer(
        "✅ <b>Рахмет!</b> Пікіріңіз қабылданды.",
        parse_mode="HTML"
    )
    
    stars = "⭐" * rating
    
    for admin in ADMIN_IDS:
        try:
            await bot.send_message(
                admin,
                f"📩 <b>Жаңа отзыв!</b>\n\n"
                f"👤 @{msg.from_user.username}\n"
                f"Бағасы: {stars}\n"
                f"Пікірі: {text}",
                parse_mode="HTML"
            )
        except:
            pass

    try:
        await bot.send_message(
            REVIEW_CHANNEL_ID,
            f"📩 <b>Жаңа отзыв!</b>\n\n"
            f"👤 @{msg.from_user.username or msg.from_user.full_name}\n"
            f"Бағасы: {stars}\n"
            f"Пікірі: {text}",
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Каналға жіберу қатесі: {e}")
            
    await state.clear()

# ---------- АДМИН ПАНЕЛЬ ----------
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
        "Формат: <code>өнім_id тариф_id KEY-1, KEY-2</code>\n"
        "Мысалы: <code>android_cry4me 1day KEY-111, KEY-222</code>",
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
            await msg.answer("❌ Қате формат немесе тариф табылмады.")
            return
        await db.add_keys(pid, plan_id, keys)
        await msg.answer(f"✅ {len(keys)} ключ қосылды!")
    except Exception as e:
        await msg.answer(f"❌ Қате: {e}")
    await state.clear()

@dp.callback_query(F.data == "profile")
async def profile(cb: CallbackQuery):
    rows = await db.user_purchases(cb.from_user.id)
    if not rows:
        text = "👤 Сатып алулар жоқ."
    else:
        text = "👤 <b>Сенің сатып алуларың:</b>\n\n"
        for product, plan, key, date in rows:
            text += f"🔑 <code>{key}</code>\n📅 {date}\n\n"
    
    await send_new_text_msg(cb, text, main_menu())
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
    webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    async def health(request):
        return web.Response(text="OK")

    app.router.add_get("/", health)
    web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)

if __name__ == "__main__":
    main()
