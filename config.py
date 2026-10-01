import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(os.getenv("ADMIN_ID", "0"))]

PRODUCTS = {
    "cry4me": {
        "name": "CRY4ME",
        "plans": {
            "1day":   {"label": "1 DAY",   "price": 1300},
            "1week":  {"label": "1 WEEK",  "price": 4500},
            "1month": {"label": "1 MONTH", "price": 15000},
        }
    },
}

KASPI_NUMBER = "4400 4300 2041 8221"
CRYPTO_WALLET = "В разработке! "
SUPPORT_URL = "https://t.me/maratovich_n"
