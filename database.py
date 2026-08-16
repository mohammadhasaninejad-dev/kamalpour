import aiosqlite
import os
import re
from config import DATABASE_PATH

async def init_db():
    os.makedirs(os.path.dirname(DATABASE_PATH) or ".", exist_ok=True)
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                excel_id TEXT,
                category TEXT,
                attr1 TEXT,
                attr2 TEXT,
                attr3 TEXT,
                attr4 TEXT,
                attr5 TEXT,
                brand TEXT,
                name TEXT,
                purchase_price REAL DEFAULT 0,
                sale_price REAL DEFAULT 0,
                wholesale_price REAL DEFAULT 0,
                sale_percent REAL,
                wholesale_percent REAL,
                stock INTEGER DEFAULT 0,
                barcode TEXT,
                seller_name TEXT,
                seller_code TEXT,
                photo_file_id TEXT,
                purchase_day INTEGER,
                purchase_month INTEGER,
                purchase_year INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                day INTEGER NOT NULL,
                month INTEGER NOT NULL,
                year INTEGER NOT NULL,
                price REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
            )
        """)

        async with db.execute("PRAGMA table_info(products)") as cursor:
            existing_cols = {row[1] for row in await cursor.fetchall()}

        migrations = {
            "excel_id": "TEXT",
            "sale_percent": "REAL",
            "wholesale_percent": "REAL",
            "purchase_day": "INTEGER",
            "purchase_month": "INTEGER",
            "purchase_year": "INTEGER",
        }
        for col, typ in migrations.items():
            if col not in existing_cols:
                await db.execute(f"ALTER TABLE products ADD COLUMN {col} {typ}")

        await db.execute("""
            UPDATE products SET excel_id = 'M-' || id
            WHERE excel_id IS NULL OR TRIM(excel_id) = ''
        """)

        await db.execute("CREATE INDEX IF NOT EXISTS idx_name ON products(name)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_barcode ON products(barcode)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_category ON products(category)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_excel_id ON products(excel_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_history_product ON price_history(product_id)")
        await db.commit()

    # پر کردن هیستوری برای کالاهای قدیمی که تاریخ/قیمت دارند
    await backfill_missing_history()


def build_product_name(category, attr1, attr2, attr3, attr4, attr5, brand, seller_name=None):
    """
    ساخت نام کالا:
    دسته + خصوصیات  /  برند  /  فروشنده
    فقط وقتی برند یا فروشنده وجود داشته باشد / گذاشته می‌شود.
    """
    parts = []
    for part in [category, attr1, attr2, attr3, attr4, attr5]:
        if part is not None and str(part).strip():
            parts.append(str(part).strip())
    base = " ".join(parts)

    suffix_parts = []
    if brand is not None and str(brand).strip():
        suffix_parts.append(str(brand).strip())
    if seller_name is not None and str(seller_name).strip():
        suffix_parts.append(str(seller_name).strip())

    if suffix_parts:
        return base + " / " + " / ".join(suffix_parts) if base else " / ".join(suffix_parts)
    return base


def _date_tuple(day, month, year):
    try:
        return (int(year or 0), int(month or 0), int(day or 0))
    except Exception:
        return (0, 0, 0)


async def add_product(data: dict) -> int:
    name = build_product_name(
        data.get("category"), data.get("attr1"), data.get("attr2"),
        data.get("attr3"), data.get("attr4"), data.get("attr5"),
        data.get("brand"), data.get("seller_name")
    )
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("""
            INSERT INTO products (
                excel_id, category, attr1, attr2, attr3, attr4, attr5, brand, name,
                purchase_price, sale_price, wholesale_price, sale_percent, wholesale_percent,
                stock, barcode, seller_name, seller_code, photo_file_id,
                purchase_day, purchase_month, purchase_year
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("excel_id"),
            data.get("category"), data.get("attr1"), data.get("attr2"),
            data.get("attr3"), data.get("attr4"), data.get("attr5"), data.get("brand"),
            name,
            data.get("purchase_price") or 0,
            data.get("sale_price") or 0,
            data.get("wholesale_price") or 0,
            data.get("sale_percent"),
            data.get("wholesale_percent"),
            data.get("stock") or 0,
            data.get("barcode"),
            data.get("seller_name"),
            data.get("seller_code"),
            data.get("photo_file_id"),
            data.get("purchase_day"),
            data.get("purchase_month"),
            data.get("purchase_year"),
        ))
        new_id = cursor.lastrowid

        if not data.get("excel_id"):
            fallback_id = f"M-{new_id}"
            await db.execute("UPDATE products SET excel_id=? WHERE id=?", (fallback_id, new_id))

        day = data.get("purchase_day")
        month = data.get("purchase_month")
        year = data.get("purchase_year")
        price = data.get("purchase_price") or 0
        if day and month and year and price:
            await db.execute("""
                INSERT INTO price_history (product_id, day, month, year, price)
                VALUES (?, ?, ?, ?, ?)
            """, (new_id, int(day), int(month), int(year), float(price)))

        await db.commit()
        return new_id


async def update_product(product_id: int, data: dict):
    name = build_product_name(
        data.get("category"), data.get("attr1"), data.get("attr2"),
        data.get("attr3"), data.get("attr4"), data.get("attr5"),
        data.get("brand"), data.get("seller_name")
    )
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            UPDATE products SET
                excel_id=?, category=?, attr1=?, attr2=?, attr3=?, attr4=?, attr5=?, brand=?, name=?,
                purchase_price=?, sale_price=?, wholesale_price=?, sale_percent=?, wholesale_percent=?,
                stock=?, barcode=?, seller_name=?, seller_code=?, photo_file_id=?,
                purchase_day=?, purchase_month=?, purchase_year=?,
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
            data.get("sale_percent"),
            data.get("wholesale_percent"),
            data.get("stock") or 0,
            data.get("barcode"),
            data.get("seller_name"),
            data.get("seller_code"),
            data.get("photo_file_id"),
            data.get("purchase_day"),
            data.get("purchase_month"),
            data.get("purchase_year"),
            product_id,
        ))
        await db.commit()


async def delete_product(product_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM price_history WHERE product_id=?", (product_id,))
        await db.execute("DELETE FROM products WHERE id=?", (product_id,))
        await db.commit()


async def get_product(product_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM products WHERE id=?", (product_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def get_product_by_name(name: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM products WHERE name=?", (name,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def get_product_by_excel_id(excel_id: str):
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


async def add_price_history(product_id: int, day: int, month: int, year: int, price: float):
    """
    افزودن رکورد هیستوری.
    اگر تاریخ جدیدتر از تاریخ خرید فعلی باشد، قیمت خرید محصول به‌روز می‌شود
    و قیمت فروش/عمده بر اساس درصدهای ذخیره‌شده دوباره محاسبه می‌شوند.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("""
            INSERT INTO price_history (product_id, day, month, year, price)
            VALUES (?, ?, ?, ?, ?)
        """, (product_id, day, month, year, price))

        async with db.execute("SELECT * FROM products WHERE id=?", (product_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                await db.commit()
                return

        product = dict(row)
        current = _date_tuple(product.get("purchase_day"), product.get("purchase_month"), product.get("purchase_year"))
        new_dt = _date_tuple(day, month, year)

        if new_dt >= current:
            purchase = float(price)
            sale_percent = product.get("sale_percent")
            wholesale_percent = product.get("wholesale_percent")

            sale = product.get("sale_price") or 0
            wholesale = product.get("wholesale_price") or 0

            if sale_percent is not None:
                try:
                    sale = purchase * (1 + float(sale_percent) / 100.0)
                except Exception:
                    pass
            if wholesale_percent is not None:
                try:
                    wholesale = purchase * (1 + float(wholesale_percent) / 100.0)
                except Exception:
                    pass

            await db.execute("""
                UPDATE products SET
                    purchase_price=?, sale_price=?, wholesale_price=?,
                    purchase_day=?, purchase_month=?, purchase_year=?,
                    updated_at=CURRENT_TIMESTAMP
                WHERE id=?
            """, (purchase, sale, wholesale, day, month, year, product_id))

        await db.commit()



async def ensure_initial_history(product_id: int, day, month, year, price):
    """اگر هیستوری‌ای برای کالا نباشد و قیمت/تاریخ داشته باشد، اولین رکورد را می‌سازد."""
    if not price or not year:
        return
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT COUNT(*) FROM price_history WHERE product_id=?", (product_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row and row[0] > 0:
                return
        try:
            d = int(day) if day else 1
            m = int(month) if month else 1
            y = int(year)
            p = float(price)
        except Exception:
            return
        await db.execute("""
            INSERT INTO price_history (product_id, day, month, year, price)
            VALUES (?, ?, ?, ?, ?)
        """, (product_id, d, m, y, p))
        await db.commit()


async def backfill_missing_history():
    """برای کالاهایی که تاریخ/قیمت دارند ولی هیستوری ندارند، اولین رکورد را بساز."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT p.id, p.purchase_day, p.purchase_month, p.purchase_year, p.purchase_price
            FROM products p
            WHERE p.purchase_price IS NOT NULL AND p.purchase_price > 0
              AND p.purchase_year IS NOT NULL
              AND NOT EXISTS (
                  SELECT 1 FROM price_history h WHERE h.product_id = p.id
              )
        """) as cursor:
            rows = await cursor.fetchall()
        for r in rows:
            day = r["purchase_day"] or 1
            month = r["purchase_month"] or 1
            year = r["purchase_year"]
            price = r["purchase_price"]
            try:
                await db.execute("""
                    INSERT INTO price_history (product_id, day, month, year, price)
                    VALUES (?, ?, ?, ?, ?)
                """, (r["id"], int(day), int(month), int(year), float(price)))
            except Exception:
                pass
        await db.commit()
        return len(rows)


async def get_price_history(product_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT * FROM price_history
            WHERE product_id=?
            ORDER BY year DESC, month DESC, day DESC, id DESC
        """, (product_id,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def get_history_item(history_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM price_history WHERE id=?", (history_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def update_price_history(history_id: int, day: int, month: int, year: int, price: float):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            UPDATE price_history SET day=?, month=?, year=?, price=?
            WHERE id=?
        """, (day, month, year, price, history_id))
        await db.commit()


async def delete_price_history(history_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM price_history WHERE id=?", (history_id,))
        await db.commit()


async def sync_product_from_latest_history(product_id: int):
    """
    بعد از ویرایش/حذف هیستوری: قیمت خرید و تاریخ کالا را از جدیدترین
    رکورد هیستوری می‌گیرد و فروش/عمده را با درصدهای ذخیره‌شده محاسبه می‌کند.
    اگر هیستوری نمانده باشد، قیمت‌ها را دست نمی‌زند (فقط تاریخ را خالی نمی‌کند اجباری).
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT * FROM price_history
            WHERE product_id=?
            ORDER BY year DESC, month DESC, day DESC, id DESC
            LIMIT 1
        """, (product_id,)) as cursor:
            latest = await cursor.fetchone()

        async with db.execute("SELECT * FROM products WHERE id=?", (product_id,)) as cursor:
            prow = await cursor.fetchone()
        if not prow:
            return
        product = dict(prow)

        if not latest:
            return

        purchase = float(latest["price"])
        day, month, year = latest["day"], latest["month"], latest["year"]
        sale = product.get("sale_price") or 0
        wholesale = product.get("wholesale_price") or 0
        sale_percent = product.get("sale_percent")
        wholesale_percent = product.get("wholesale_percent")
        if sale_percent is not None:
            try:
                sale = purchase * (1 + float(sale_percent) / 100.0)
            except Exception:
                pass
        if wholesale_percent is not None:
            try:
                wholesale = purchase * (1 + float(wholesale_percent) / 100.0)
            except Exception:
                pass

        await db.execute("""
            UPDATE products SET
                purchase_price=?, sale_price=?, wholesale_price=?,
                purchase_day=?, purchase_month=?, purchase_year=?,
                updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        """, (purchase, sale, wholesale, day, month, year, product_id))
        await db.commit()



FA_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
AR_DIGITS = "٠١٢٣٤٥٦٧٨٩"
EN_DIGITS = "0123456789"
_DIGIT_MAP = str.maketrans(FA_DIGITS + AR_DIGITS, EN_DIGITS * 2)


def _normalize_fa(text: str) -> str:
    if not text:
        return ""
    text = str(text).replace("ي", "ی").replace("ك", "ک")
    text = text.translate(_DIGIT_MAP)
    text = text.replace("\u200c", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_digits(text: str) -> str:
    if text is None:
        return ""
    return str(text).translate(_DIGIT_MAP)


def _norm_col(col: str) -> str:
    expr = f"COALESCE({col}, '')"
    pairs = [("ي", "ی"), ("ك", "ک"), ("\u200c", " ")]
    pairs += list(zip(FA_DIGITS, EN_DIGITS)) + list(zip(AR_DIGITS, EN_DIGITS))
    for frm, to in pairs:
        expr = f"REPLACE({expr}, '{frm}', '{to}')"
    return expr


def _search_where_cols(query: str, cols: list):
    words = [w for w in _normalize_fa(query).split(" ") if w]
    if not words:
        words = [""]
    clauses = []
    params = []
    for w in words:
        like = f"%{w}%"
        sub = " OR ".join(f"{_norm_col(c)} LIKE ?" for c in cols)
        clauses.append(f"({sub})")
        params.extend([like] * len(cols))
    where_sql = " AND ".join(clauses)
    return where_sql, params


def _search_where(query: str):
    return _search_where_cols(query, ["name", "barcode", "category", "brand", "seller_name"])


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


async def search_by_seller(query: str, offset: int = 0, limit: int = 10):
    where_sql, params = _search_where_cols(query, ["seller_name"])
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        sql = f"SELECT * FROM products WHERE {where_sql} ORDER BY name LIMIT ? OFFSET ?"
        async with db.execute(sql, (*params, limit, offset)) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def count_by_seller(query: str) -> int:
    where_sql, params = _search_where_cols(query, ["seller_name"])
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


async def get_all_products_full():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM products ORDER BY id") as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def count_products() -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM products") as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0


async def clear_products():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM price_history")
        await db.execute("DELETE FROM products")
        await db.commit()


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
