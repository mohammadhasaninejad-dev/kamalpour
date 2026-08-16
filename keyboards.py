from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
    WebAppInfo
)
from config import WEBAPP_URL


def main_menu(is_admin: bool = False):
    buttons = [
        [
            KeyboardButton(text="🔍 استعلام متنی"),
            KeyboardButton(
                text="📷 استعلام تصویری",
                web_app=WebAppInfo(url=f"{WEBAPP_URL.rstrip('/')}/scanner")
            ),
        ],
    ]
    if is_admin:
        buttons.append([
            KeyboardButton(text="📋 لیست کالا بر اساس دسته"),
            KeyboardButton(text="👤 جستجو بر اساس فروشنده"),
        ])
        buttons.append([KeyboardButton(text="📦 مدیریت کالا")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def admin_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ افزودن کالا"), KeyboardButton(text="✏️ ویرایش کالا")],
            [KeyboardButton(text="🗑 حذف کالا"), KeyboardButton(text="🔎 جستجو بر اساس شناسه")],
            [KeyboardButton(text="📋 لیست کالاها")],
            [KeyboardButton(text="📥 ایمپورت اکسل"), KeyboardButton(text="📤 خروجی اکسل")],
            [KeyboardButton(text="🧨 پاک کردن کامل دیتابیس")],
            [KeyboardButton(text="🔙 بازگشت به منوی اصلی")],
        ],
        resize_keyboard=True
    )


def cancel_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ انصراف")]],
        resize_keyboard=True
    )


def skip_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⏭ رد کردن")],
            [KeyboardButton(text="❌ انصراف")],
        ],
        resize_keyboard=True
    )


def barcode_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(
                text="📷 اسکن بارکد",
                web_app=WebAppInfo(url=f"{WEBAPP_URL.rstrip('/')}/scanner")
            )],
            [KeyboardButton(text="⏭ رد کردن")],
            [KeyboardButton(text="❌ انصراف")],
        ],
        resize_keyboard=True
    )


def year_suggest_kb(current_year: int = 1405):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=str(current_year))],
            [KeyboardButton(text="⏭ رد کردن")],
            [KeyboardButton(text="❌ انصراف")],
        ],
        resize_keyboard=True
    )


def product_actions_kb(product_id: int, is_admin: bool = False):
    buttons = []
    # همه می‌توانند هیستوری را ببینند
    buttons.append([
        InlineKeyboardButton(text="📜 نمایش هیستوری", callback_data=f"showhist:{product_id}"),
    ])
    if is_admin:
        buttons.insert(0, [
            InlineKeyboardButton(text="✏️ ویرایش", callback_data=f"edit:{product_id}"),
            InlineKeyboardButton(text="🗑 حذف", callback_data=f"del:{product_id}"),
        ])
        buttons.append([
            InlineKeyboardButton(text="➕ هیستوری", callback_data=f"addhist:{product_id}"),
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def history_item_kb(history_id: int, product_id: int, is_admin: bool = False):
    """دکمه‌های ویرایش/حذف برای یک رکورد هیستوری"""
    if not is_admin:
        return None
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️", callback_data=f"edithist:{history_id}"),
            InlineKeyboardButton(text="🗑", callback_data=f"delhist:{history_id}:{product_id}"),
        ]
    ])


def confirm_delete_history_kb(history_id: int, product_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ بله، حذف شود", callback_data=f"confirm_delhist:{history_id}:{product_id}"),
            InlineKeyboardButton(text="❌ خیر", callback_data="cancel_delhist"),
        ]
    ])


def pagination_kb(page: int, total: int, page_size: int = 10):
    buttons = []
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="◀️ قبلی", callback_data=f"page:{page-1}"))
    if (page + 1) * page_size < total:
        nav.append(InlineKeyboardButton(text="بعدی ▶️", callback_data=f"page:{page+1}"))
    if nav:
        buttons.append(nav)
    return InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None


def results_kb(products: list, page: int, total: int, page_size: int, nav_prefix: str = "page"):
    buttons = []
    for p in products:
        text = p.get("name") or "بدون نام"
        if len(text) > 60:
            text = text[:59] + "…"
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"viewp:{p['id']}")])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="◀️ قبلی", callback_data=f"{nav_prefix}:{page-1}"))
    if (page + 1) * page_size < total:
        nav.append(InlineKeyboardButton(text="بعدی ▶️", callback_data=f"{nav_prefix}:{page+1}"))
    if nav:
        buttons.append(nav)

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def list_products_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏷 مرور بر اساس دسته", callback_data="browse_by_category")],
        [InlineKeyboardButton(text="👤 جستجو بر اساس فروشنده", callback_data="browse_by_seller")],
    ])


def confirm_delete_kb(product_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ بله، حذف شود", callback_data=f"confirm_del:{product_id}"),
            InlineKeyboardButton(text="❌ خیر", callback_data="cancel_del"),
        ]
    ])


def confirm_wipe_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🧨 بله، همه چیز پاک شود", callback_data="confirm_wipe"),
            InlineKeyboardButton(text="❌ نه، انصراف", callback_data="cancel_wipe"),
        ]
    ])


def edit_fields_kb(product_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="دسته", callback_data=f"efield:{product_id}:category"),
            InlineKeyboardButton(text="برند", callback_data=f"efield:{product_id}:brand"),
        ],
        [
            InlineKeyboardButton(text="خصوصیت ۱", callback_data=f"efield:{product_id}:attr1"),
            InlineKeyboardButton(text="خصوصیت ۲", callback_data=f"efield:{product_id}:attr2"),
        ],
        [
            InlineKeyboardButton(text="خصوصیت ۳", callback_data=f"efield:{product_id}:attr3"),
            InlineKeyboardButton(text="خصوصیت ۴", callback_data=f"efield:{product_id}:attr4"),
        ],
        [
            InlineKeyboardButton(text="خصوصیت ۵", callback_data=f"efield:{product_id}:attr5"),
            InlineKeyboardButton(text="بارکد", callback_data=f"efield:{product_id}:barcode"),
        ],
        [
            InlineKeyboardButton(text="قیمت خرید", callback_data=f"efield:{product_id}:purchase_price"),
            InlineKeyboardButton(text="قیمت فروش (٪)", callback_data=f"efield:{product_id}:sale_price"),
        ],
        [
            InlineKeyboardButton(text="قیمت عمده (٪)", callback_data=f"efield:{product_id}:wholesale_price"),
            InlineKeyboardButton(text="موجودی", callback_data=f"efield:{product_id}:stock"),
        ],
        [
            InlineKeyboardButton(text="فروشنده", callback_data=f"efield:{product_id}:seller_name"),
            InlineKeyboardButton(text="کد فروشنده", callback_data=f"efield:{product_id}:seller_code"),
        ],
        [
            InlineKeyboardButton(text="روز خرید", callback_data=f"efield:{product_id}:purchase_day"),
            InlineKeyboardButton(text="ماه خرید", callback_data=f"efield:{product_id}:purchase_month"),
        ],
        [
            InlineKeyboardButton(text="سال خرید", callback_data=f"efield:{product_id}:purchase_year"),
            InlineKeyboardButton(text="🖼 عکس", callback_data=f"efield:{product_id}:photo_file_id"),
        ],
        [
            InlineKeyboardButton(text="❌ انصراف", callback_data="cancel_edit"),
        ],
    ])


def browse_categories_kb(categories: list, page: int = 0, page_size: int = 8):
    start = page * page_size
    chunk = list(enumerate(categories))[start:start + page_size]
    buttons = []
    row = []
    for idx, cat in chunk:
        row.append(InlineKeyboardButton(text=cat, callback_data=f"browsecat:{idx}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="◀️ قبلی", callback_data=f"browsecatpage:{page-1}"))
    if start + page_size < len(categories):
        nav.append(InlineKeyboardButton(text="بعدی ▶️", callback_data=f"browsecatpage:{page+1}"))
    if nav:
        buttons.append(nav)

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def browse_attrs_kb(attrs: list, page: int = 0, page_size: int = 8):
    start = page * page_size
    chunk = list(enumerate(attrs))[start:start + page_size]
    buttons = []
    row = []
    for idx, a in chunk:
        row.append(InlineKeyboardButton(text=str(a), callback_data=f"browseattr:{idx}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="◀️ قبلی", callback_data=f"browseattrpage:{page-1}"))
    if start + page_size < len(attrs):
        nav.append(InlineKeyboardButton(text="بعدی ▶️", callback_data=f"browseattrpage:{page+1}"))
    if nav:
        buttons.append(nav)

    buttons.append([InlineKeyboardButton(text="🔙 دسته‌ها", callback_data="browseback:cat")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def browse_products_nav_kb(page: int, total: int, page_size: int, has_attr: bool):
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="◀️ قبلی", callback_data=f"browsepage:{page-1}"))
    if (page + 1) * page_size < total:
        nav.append(InlineKeyboardButton(text="بعدی ▶️", callback_data=f"browsepage:{page+1}"))

    buttons = []
    if nav:
        buttons.append(nav)
    back_target = "browseback:attr" if has_attr else "browseback:cat"
    back_text = "🔙 خصوصیت‌ها" if has_attr else "🔙 دسته‌ها"
    buttons.append([InlineKeyboardButton(text=back_text, callback_data=back_target)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def back_to_admin_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 بازگشت به مدیریت کالا")]],
        resize_keyboard=True
    )
