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
                excel_id TEXT,              -- ستون «شناسه» اکسل؛ برای تشخیص دقیق کالای تکراری هنگام ایمپورت
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

        # مهاجرت برای دیتابیس‌های قدیمی که از قبل ساخته شده‌اند و ستون excel_id را ندارند
        async with db.execute("PRAGMA table_info(products)") as cursor:
            existing_cols = {row[1] for row in await cursor.fetchall()}
        if "excel_id" not in existing_cols:
            await db.execute("ALTER TABLE products ADD COLUMN excel_id TEXT")

        # پرکردن شناسه برای کالاهای قدیمی‌ای که قبل از این تغییر بدون excel_id ثبت شده‌اند
        await db.execute("""
            UPDATE products SET excel_id = 'M-' || id
            WHERE excel_id IS NULL OR TRIM(excel_id) = ''
        """)

        await db.execute("CREATE INDEX IF NOT EXISTS idx_name ON products(name)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_barcode ON products(barcode)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_category ON products(category)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_excel_id ON products(excel_id)")
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
                excel_id, category, attr1, attr2, attr3, attr4, attr5, brand, name,
                purchase_price, sale_price, wholesale_price, stock, barcode,
                seller_name, seller_code, photo_file_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("excel_id"),
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
        new_id = cursor.lastrowid

        # کالاهایی که از اکسل نیامده‌اند (مثلاً با «➕ افزودن کالا» دستی ثبت شده‌اند) ستون
        # excel_id خالی دارند. چون این ستون تنها شناسه‌ای است که به کاربر نمایش داده
        # می‌شود و برای ویرایش/حذف با آن جست‌وجو می‌کنیم، باید همیشه پر باشد؛ پیشوند
        # "M-" هم تضمین می‌کند با هیچ شناسه‌ی عددیِ اکسل تداخل پیدا نکند.
        if not data.get("excel_id"):
            fallback_id = f"M-{new_id}"
            await db.execute("UPDATE products SET excel_id=? WHERE id=?", (fallback_id, new_id))

        await db.commit()
        return new_id


async def update_product(product_id: int, data: dict):
    name = build_product_name(
        data.get("category"), data.get("attr1"), data.get("attr2"),
        data.get("attr3"), data.get("attr4"), data.get("attr5"), data.get("brand")
    )
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            UPDATE products SET
                excel_id=?, category=?, attr1=?, attr2=?, attr3=?, attr4=?, attr5=?, brand=?, name=?,
                purchase_price=?, sale_price=?, wholesale_price=?, stock=?, barcode=?,
                seller_name=?, seller_code=?, photo_file_id=?,
                updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        """, (
            data.get("excel_id"),
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


async def get_product_by_excel_id(excel_id: str):
    """
    برای تطبیق سطرهای اکسل با کالاهای موجود بر اساس ستون «شناسه» اکسل.
    برخلاف تطبیق بر اساس نام، حتی اگر چند کالای مختلف دسته/خصوصیت/برند یکسانی
    داشته باشند (که باعث ساخته‌شدن نام یکسان می‌شود) باز هم درست تشخیص داده می‌شوند،
    چون شناسه اکسل برای هر ردیف منحصربه‌فرد است.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM products WHERE excel_id=?", (str(excel_id),)) as cursor:
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


# ---------- مرور کالاها بر اساس دسته / خصوصیت ۱ (برای «📋 لیست کالاها») ----------

async def get_distinct_categories():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("""
            SELECT DISTINCT category FROM products
            WHERE category IS NOT NULL AND TRIM(category) != ''
            ORDER BY category
        """) as cursor:
            rows = await cursor.fetchall()
            return [r[0] for r in rows]


async def get_distinct_attr1(category: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("""
            SELECT DISTINCT attr1 FROM products
            WHERE category=? AND attr1 IS NOT NULL AND TRIM(attr1) != ''
            ORDER BY attr1
        """, (category,)) as cursor:
            rows = await cursor.fetchall()
            return [r[0] for r in rows]


async def get_products_by_category_attr1(category: str, attr1, offset: int = 0, limit: int = 10):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        if attr1 is None:
            sql = "SELECT * FROM products WHERE category=? ORDER BY name LIMIT ? OFFSET ?"
            params = (category, limit, offset)
        else:
            sql = "SELECT * FROM products WHERE category=? AND attr1=? ORDER BY name LIMIT ? OFFSET ?"
            params = (category, attr1, limit, offset)
        async with db.execute(sql, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def count_products_by_category_attr1(category: str, attr1) -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        if attr1 is None:
            sql = "SELECT COUNT(*) FROM products WHERE category=?"
            params = (category,)
        else:
            sql = "SELECT COUNT(*) FROM products WHERE category=? AND attr1=?"
            params = (category, attr1)
        async with db.execute(sql, params) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0