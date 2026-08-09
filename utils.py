from config import ADMINS, ADMIN_IDS


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
        return f"{int(v):,}".replace(",", "٬") + " تومان"
    except Exception:
        return "—"


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

    lines.extend([
        f"💰 قیمت فروش: {format_price(product.get('sale_price'))}",
        f"📦 قیمت عمده: {format_price(product.get('wholesale_price'))}",
        f"📥 قیمت خرید: {format_price(product.get('purchase_price'))}",
        f"📊 موجودی: {product.get('stock') or 0}",
        f"🔢 بارکد: {product.get('barcode') or '—'}",
        f"👤 فروشنده: {product.get('seller_name') or '—'} ({product.get('seller_code') or '—'})",
        f"🆔 شناسه: {excel_id}",
    ])
    return "\n".join(lines)