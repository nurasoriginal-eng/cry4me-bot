import aiosqlite

DB = "shop.db"

async def init_db():
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS keys_stock (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product TEXT,
                plan TEXT,
                key_value TEXT UNIQUE,
                is_sold INTEGER DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                product TEXT,
                plan TEXT,
                key_value TEXT,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

async def add_keys(product, plan, keys):
    async with aiosqlite.connect(DB) as db:
        for k in keys:
            try:
                await db.execute(
                    "INSERT INTO keys_stock (product, plan, key_value) VALUES (?,?,?)",
                    (product, plan, k.strip())
                )
            except:
                pass
        await db.commit()

async def get_key(product, plan):
    async with aiosqlite.connect(DB) as db:
        async with db.execute(
            "SELECT id, key_value FROM keys_stock WHERE product=? AND plan=? AND is_sold=0 LIMIT 1",
            (product, plan)
        ) as cur:
            row = await cur.fetchone()
            if not row:
                return None
            await db.execute("UPDATE keys_stock SET is_sold=1 WHERE id=?", (row[0],))
            await db.commit()
            return row[1]

async def count_stock(product, plan):
    async with aiosqlite.connect(DB) as db:
        async with db.execute(
            "SELECT COUNT(*) FROM keys_stock WHERE product=? AND plan=? AND is_sold=0",
            (product, plan)
        ) as cur:
            return (await cur.fetchone())[0]

async def save_purchase(user_id, product, plan, key_value):
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "INSERT INTO purchases (user_id, product, plan, key_value) VALUES (?,?,?,?)",
            (user_id, product, plan, key_value)
        )
        await db.commit()

async def user_purchases(user_id):
    async with aiosqlite.connect(DB) as db:
        async with db.execute(
            "SELECT product, plan, key_value, date FROM purchases WHERE user_id=? ORDER BY id DESC",
            (user_id,)
        ) as cur:
            return await cur.fetchall()

async def get_all_orders():
    async with aiosqlite.connect(DB) as db:
        async with db.execute(
            "SELECT id, user_id, product, plan, key_value, date FROM purchases ORDER BY id DESC LIMIT 50"
        ) as cur:
            return await cur.fetchall()
