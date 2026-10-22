import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(os.getenv("ADMIN_ID", "0"))]

# БАСТЫ БЕТТІҢ СУРЕТІ (PRIVATE SOFT) - Осы жерге өз сілтемеңді қой
MAIN_PHOTO = "https://i.ibb.co/Vc-YR0Xs/B71BDE16-0D70-4405-8361-D4BCDEF90701.jpg" 

# ANDROID БЕТІНІҢ СУРЕТІ (ANDROID NROOT)
ANDROID_PHOTO = "https://ibb.co.com/GQpgcnPH"

PRODUCTS = {
    # --- ANDROID NROOT (БЕЗ РУТ) ---
    "android_magic_vip": {
        "name": "MAGIC VIP",
        "platform": "android",
        "photo": "https://ibb.co.com/h1FDZbkM",
        "in_dev": True,
        "plans": {}
    },
    "android_magic_lite": {
        "name": "MAGIC LITE",
        "platform": "android",
        "photo": "https://ibb.co.com/3y6F3kQJ",
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
        "photo": "https://ibb.co.com/gbxTNsr3",
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
        "photo": "https://i.ibb.co/VcpYR0Xs/B71BDE16-0D70-4405-8361-D4BCDEF90701.jpg", # Осы жерге iOS суретін қоюға болады
        "in_dev": True,
        "plans": {}
    },
}

KASPI_NUMBER = "4400 4300 2041 8221"
CRYPTO_WALLET = "В разработке"
SUPPORT_URL = "https://t.me/maratovich_n"
