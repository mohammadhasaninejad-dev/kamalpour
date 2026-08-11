from config import ADMINS, ADMIN_IDS
from database import normalize_digits


def is_admin(user) -> bool:
    if not user:
        return False
    if user.id in ADMIN_IDS:
        return True
    if user.username and user.username.lower() in [a.lower() for a in ADMINS]:
        return True
    return False


def format_price(value) -> str:
    try:
        v = float(value or 0)
        if v == 0:
            return "—"
        return f"{int(round(v)):,}".replace(",", "٬") + " تومان"
    except Exception:
        return "—"


def format_date(day, month, year) -> str:
    if not year:
        return "—"
    d = day or "—"
    m = month or "—"
    return f"{d}/{m}/{year}"


def format_product(product: dict, short: bool = False) -> str:
    name = product.get("name") or "بدون نام"
    excel_id = product.get("excel_id") or "—"
    if short:
        return f"🆔 {excel_id} | {name}"

    lines = [
        f"📦 <b>{name}</b>",
        f"🏷 دسته: {product.get('category') or '—'}",
    ]
    attrs = []
    for i in range(1, 6):
        a = product.get(f"attr{i}")
        if a:
            attrs.append(str(a))
    if attrs:
        lines.append(f"🔹 خصوصیات: {' | '.join(attrs)}")
    if product.get("brand"):
        lines.append(f"🏷 برند: {product['brand']}")

    purchase_date = format_date(
        product.get("purchase_day"),
        product.get("purchase_month"),
        product.get("purchase_year"),
    )

    lines.extend([
        f"💰 قیمت فروش: {format_price(product.get('sale_price'))}",
        f"📦 قیمت عمده: {format_price(product.get('wholesale_price'))}",
        f"📥 قیمت خرید: {format_price(product.get('purchase_price'))}",
        f"📅 تاریخ خرید: {purchase_date}",
        f"🔢 بارکد: {product.get('barcode') or '—'}",
        f"👤 فروشنده: {product.get('seller_name') or '—'} ({product.get('seller_code') or '—'})",
        f"🆔 شناسه: {excel_id}",
    ])

    # نمایش درصدها اگر موجود باشند
    sp = product.get("sale_percent")
    wp = product.get("wholesale_percent")
    if sp is not None or wp is not None:
        pct_parts = []
        if sp is not None:
            pct_parts.append(f"فروش {sp}%")
        if wp is not None:
            pct_parts.append(f"عمده {wp}%")
        lines.append(f"📊 درصد سود: {' | '.join(pct_parts)}")

    return "\n".join(lines)


def parse_number(text: str):
    """پارس عدد با پشتیبانی از ارقام فارسی و انگلیسی و جداکننده هزارگان"""
    if text is None:
        return None
    if text == "⏭ رد کردن":
        return 0
    cleaned = normalize_digits(text)
    cleaned = cleaned.replace(",", "").replace("٬", "").replace(" ", "").strip()
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except Exception:
        return None


def parse_int(text: str):
    """پارس عدد صحیح با پشتیبانی ارقام فارسی"""
    if text is None:
        return None
    cleaned = normalize_digits(text).replace(",", "").replace("٬", "").replace(" ", "").strip()
    if not cleaned:
        return None
    try:
        return int(float(cleaned))
    except Exception:
        return None
