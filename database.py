import aiosqlite
import os
import re
from config import DATABASE_PATH

async def init_db():
    os.makedirs(os.path.dirname(DATABASE_PATH) or ".", exist_ok=True)
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # WAL باعث می‌شود خواندن و نوشتن هم‌زمان (مثلاً جستجو حین ثبت کالا) قفل نشوند
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT,
                attr1 TEXT,
                attr2 TEXT,
                attr3 TEXT,
                attr4 TEXT,
                attr5 TEXT,
                brand TEXT,
                name TEXT,                  -- نام کامل ساخته‌شده
                purchase_price REAL DEFAULT 0,
                sale_price REAL DEFAULT 0,
                wholesale_price REAL DEFAULT 0,
                stock INTEGER DEFAULT 0,
                barcode TEXT,
                seller_name TEXT,
                seller_code TEXT,
                photo_file_id TEXT,         -- file_id تلگرام
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("CREATE INDEX IF NOT EXISTS idx_name ON products(name)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_barcode ON products(barcode)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_category ON products(category)")
        await db.commit()


def build_product_name(category, attr1, attr2, attr3, attr4, attr5, brand):
    """ساخت نام کالا از ترکیب فیلدها بدون جداکننده خاص"""
    parts = []
    for part in [category, attr1, attr2, attr3, attr4, attr5, brand]:
        if part is not None and str(part).strip():
            parts.append(str(part).strip())
    return " ".join(parts)


async def add_product(data: dict) -> int:
    name = build_product_name(
        data.get("category"), data.get("attr1"), data.get("attr2"),
        data.get("attr3"), data.get("attr4"), data.get("attr5"), data.get("brand")
    )
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("""
            INSERT INTO products (
                category, attr1, attr2, attr3, attr4, attr5, brand, name,
                purchase_price, sale_price, wholesale_price, stock, barcode,
                seller_name, seller_code, photo_file_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("category"), data.get("attr1"), data.get("attr2"),
            data.get("attr3"), data.get("attr4"), data.get("attr5"), data.get("brand"),
            name,
            data.get("purchase_price") or 0,
            data.get("sale_price") or 0,
            data.get("wholesale_price") or 0,
            data.get("stock") or 0,
            data.get("barcode"),
            data.get("seller_name"),
            data.get("seller_code"),
            data.get("photo_file_id"),
        ))
        await db.commit()
        return cursor.lastrowid


async def update_product(product_id: int, data: dict):
    name = build_product_name(
        data.get("category"), data.get("attr1"), data.get("attr2"),
        data.get("attr3"), data.get("attr4"), data.get("attr5"), data.get("brand")
    )
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            UPDATE products SET
                category=?, attr1=?, attr2=?, attr3=?, attr4=?, attr5=?, brand=?, name=?,
                purchase_price=?, sale_price=?, wholesale_price=?, stock=?, barcode=?,
                seller_name=?, seller_code=?, photo_file_id=?,
                updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        """, (
            data.get("category"), data.get("attr1"), data.get("attr2"),
            data.get("attr3"), data.get("attr4"), data.get("attr5"), data.get("brand"),
            name,
            data.get("purchase_price") or 0,
            data.get("sale_price") or 0,
            data.get("wholesale_price") or 0,
            data.get("stock") or 0,
            data.get("barcode"),
            data.get("seller_name"),
            data.get("seller_code"),
            data.get("photo_file_id"),
            product_id,
        ))
        await db.commit()


async def delete_product(product_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM products WHERE id=?", (product_id,))
        await db.commit()


async def get_product(product_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM products WHERE id=?", (product_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def get_product_by_name(name: str):
    """برای تطبیق سطرهای اکسل با کالاهای موجود، تا هنگام ایمپورت بارکد/موجودی/عکس پاک نشود"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM products WHERE name=?", (name,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def get_product_by_barcode(barcode: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM products WHERE barcode=?", (barcode,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


def _normalize_fa(text: str) -> str:
    """یکسان‌سازی کاراکترهای عربی/فارسی رایج و نیم‌فاصله، تا جستجو به تفاوت رسم‌الخط حساس نباشد"""
    if not text:
        return ""
    text = str(text).replace("ي", "ی").replace("ك", "ک")
    text = text.replace("\u200c", " ")  # نیم‌فاصله -> فاصله
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _norm_col(col: str) -> str:
    """همان نرمال‌سازی بالا ولی به‌صورت عبارت SQL، برای اعمال روی مقدار ذخیره‌شده در دیتابیس"""
    return f"REPLACE(REPLACE(REPLACE(COALESCE({col}, ''), 'ي', 'ی'), 'ك', 'ک'), char(8204), ' ')"


def _search_where(query: str):
    """
    جستجوی هوشمند: عبارت به کلمه‌ها شکسته می‌شود و هر کلمه باید یک‌جایی در
    نام/دسته/برند/بارکد کالا پیدا شود - نه لزوماً پشت‌سرهم. یعنی اگر کاربر فقط
    اولین و آخرین کلمه‌ی نام کالا را با فاصله بنویسد (مثلاً «دفتر آبی» برای
    «دفتر ۱۰۰برگ رحلی آبی»)، باز هم پیدا می‌شود.
    """
    words = [w for w in _normalize_fa(query).split(" ") if w]
    if not words:
        words = [""]
    cols = ["name", "barcode", "category", "brand"]
    clauses = []
    params = []
    for w in words:
        like = f"%{w}%"
        sub = " OR ".join(f"{_norm_col(c)} LIKE ?" for c in cols)
        clauses.append(f"({sub})")
        params.extend([like] * len(cols))
    where_sql = " AND ".join(clauses)
    return where_sql, params


async def search_products(query: str, offset: int = 0, limit: int = 10):
    where_sql, params = _search_where(query)
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        sql = f"SELECT * FROM products WHERE {where_sql} ORDER BY name LIMIT ? OFFSET ?"
        async with db.execute(sql, (*params, limit, offset)) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def count_search(query: str) -> int:
    where_sql, params = _search_where(query)
    async with aiosqlite.connect(DATABASE_PATH) as db:
        sql = f"SELECT COUNT(*) FROM products WHERE {where_sql}"
        async with db.execute(sql, params) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0


async def get_all_products(offset: int = 0, limit: int = 20):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT * FROM products ORDER BY id DESC LIMIT ? OFFSET ?
        """, (limit, offset)) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def count_products() -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM products") as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0


async def clear_products():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM products")
        await db.commit()