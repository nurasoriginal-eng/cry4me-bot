import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(os.getenv("ADMIN_ID", "0"))]

# --- СУРЕТТЕРДІҢ ТІКЕЛЕЙ СІЛТЕМЕЛЕРІ ---
MAIN_PHOTO = "https://i.ibb.co/VcpYR0Xs/B71BDE16-0D70-4405-8361-D4BCDEF90701.jpg"
ANDROID_PHOTO = "https://i.ibb.co/GQpgcnPH/IMG-8349.jpg"

PRODUCTS = {
    # --- ANDROID NROOT (БЕЗ РУТ) ---
    "android_magic_vip": {
        "name": "MAGIC VIP",
        "platform": "android",
        "photo": "https://i.ibb.co/5hTJQS41/93A0EA42-A893-4A85-B66A-650254A16AB7.jpg", 
        "in_dev": True,
        "plans": {}
    },
    "android_magic_lite": {
        "name": "MAGIC LITE",
        "platform": "android",
        "photo": "https://i.ibb.co/s8SHyK7/IMG-8349.jpg",
        "in_dev": False,
        "description": (
            "Функциональный и стабильный софт для игры.\n"
            "Отличный выбор для комфортной игры без лишних нагрузок."
        ),
        "plans": {
            "1day":   {"label": "MAGIC LITE день",   "price": 800},
            "1week":  {"label": "MAGIC LITE 7 дней", "price": 3000},
            "1month": {"label": "MAGIC LITE 30 дней","price": 9000},
        }
    },
    "android_cry4me": {
        "name": "CRY4ME",
        "platform": "android",
        "photo": "https://i.ibb.co/VcpYR0Xs/B71BDE16-0D70-4405-8361-D4BCDEF90701.jpg",
        "in_dev": False,
        "description": (
            "Один из самых популярных и функциональных клиентов для Oxide Survival Island.\n\n"
            "Описание функций на скрине выше\n"
            "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
            "├ Поддержка Android 10,11,12,13,14,15,16 - 64BIT\n"
            "├ Кастомное меню (можно включать определенные функции по одному) Полностью безопасно.\n"
            "└ Работает на оригинальной игре"
        ),
        "plans": {
            "1day":   {"label": "CRY4ME день",   "price": 1100},
            "1week":  {"label": "CRY4ME 7 дней", "price": 4100},
            "1month": {"label": "CRY4ME 30 дней","price": 11500},
        }
    },
    
    # --- IOS (iPhone) ---
    "ios_aqreh": {
        "name": "AQREH",
        "platform": "ios",
        "photo": "https://i.ibb.co/VcpYR0Xs/B71BDE16-0D70-4405-8361-D4BCDEF90701.jpg", 
        "in_dev": True,
        "plans": {}
    },
}

KASPI_NUMBER = "4400 4300 2041 8221" # ӨЗ НӨМІРІҢДІ ҚОЙ
CRYPTO_WALLET = "В разработке!" # ӨЗ ӘМИЯНЫҢДЫ ҚОЙ
SUPPORT_URL = "https://t.me/maratovich_n" # ӨЗ ЮЗЕРНЕЙМІҢДІ ҚОЙ
