from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
    WebAppInfo
)
from config import WEBAPP_URL


def main_menu(is_admin: bool = False):
    buttons = [
        [KeyboardButton(text="🔍 استعلام متنی"), KeyboardButton(text="📷 استعلام تصویری")],
    ]
    if is_admin:
        buttons.append([KeyboardButton(text="📦 مدیریت کالا")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def admin_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ افزودن کالا"), KeyboardButton(text="✏️ ویرایش کالا")],
            [KeyboardButton(text="🗑 حذف کالا"), KeyboardButton(text="📋 لیست کالاها")],
            [KeyboardButton(text="📥 ایمپورت اکسل"), KeyboardButton(text="🔙 بازگشت به منوی اصلی")],
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


def barcode_webapp_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(
                text="📷 باز کردن اسکنر بارکد",
                web_app=WebAppInfo(url=f"{WEBAPP_URL}/scanner")
            )],
            [KeyboardButton(text="🔙 بازگشت به منوی اصلی")],
        ],
        resize_keyboard=True
    )


def product_actions_kb(product_id: int, is_admin: bool = False):
    buttons = []
    if is_admin:
        buttons.append([
            InlineKeyboardButton(text="✏️ ویرایش", callback_data=f"edit:{product_id}"),
            InlineKeyboardButton(text="🗑 حذف", callback_data=f"del:{product_id}"),
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None


def pagination_kb(query: str, page: int, total: int, page_size: int = 10):
    buttons = []
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="◀️ قبلی", callback_data=f"page:{query}:{page-1}"))
    if (page + 1) * page_size < total:
        nav.append(InlineKeyboardButton(text="بعدی ▶️", callback_data=f"page:{query}:{page+1}"))
    if nav:
        buttons.append(nav)
    return InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None


def confirm_delete_kb(product_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ بله، حذف شود", callback_data=f"confirm_del:{product_id}"),
            InlineKeyboardButton(text="❌ خیر", callback_data="cancel_del"),
        ]
    ])


def back_to_admin_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 بازگشت به مدیریت کالا")]],
        resize_keyboard=True
    )