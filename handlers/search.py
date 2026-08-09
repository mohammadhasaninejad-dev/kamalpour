from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ContentType
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from states import TextSearch
from keyboards import main_menu, barcode_webapp_kb, pagination_kb, product_actions_kb, cancel_kb
from database import search_products, count_search, get_product_by_barcode, get_product
from utils import is_admin, format_product
from config import PAGE_SIZE

router = Router()


# ---------- استعلام متنی ----------
@router.message(F.text == "🔍 استعلام متنی")
async def text_search_start(message: Message, state: FSMContext):
    await state.set_state(TextSearch.waiting_query)
    await message.answer(
        "نام کالا یا بخشی از آن را بنویسید:\n"
        "(مثال: دفتر ۱۶۰ یا خودکار بیک)",
        reply_markup=cancel_kb()
    )


@router.message(TextSearch.waiting_query, F.text == "❌ انصراف")
async def text_search_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("لغو شد.", reply_markup=main_menu(is_admin(message.from_user)))


@router.message(TextSearch.waiting_query)
async def text_search_query(message: Message, state: FSMContext):
    query = message.text.strip()
    if not query:
        await message.answer("لطفاً متنی وارد کنید.")
        return

    total = await count_search(query)
    if total == 0:
        await message.answer(
            "❌ هیچ کالایی پیدا نشد.\nمتن دیگری امتحان کنید یا انصراف بزنید.",
            reply_markup=cancel_kb()
        )
        return

    await state.update_data(search_query=query)
    products = await search_products(query, offset=0, limit=PAGE_SIZE)
    admin = is_admin(message.from_user)

    await message.answer(f"🔍 نتایج برای «{query}» ({total} مورد):")
    for p in products:
        text = format_product(p)
        kb = product_actions_kb(p["id"], admin)
        if p.get("photo_file_id"):
            await message.answer_photo(p["photo_file_id"], caption=text, parse_mode="HTML", reply_markup=kb)
        else:
            await message.answer(text, parse_mode="HTML", reply_markup=kb)

    if total > PAGE_SIZE:
        await message.answer(
            "صفحات بیشتر:",
            reply_markup=pagination_kb(query, 0, total, PAGE_SIZE)
        )


@router.callback_query(F.data.startswith("page:"))
async def pagination_handler(callback: CallbackQuery):
    try:
        _, query, page_str = callback.data.split(":", 2)
        page = int(page_str)
    except Exception:
        await callback.answer("خطا در صفحه‌بندی")
        return

    total = await count_search(query)
    products = await search_products(query, offset=page * PAGE_SIZE, limit=PAGE_SIZE)
    admin = is_admin(callback.from_user)

    await callback.message.answer(f"🔍 صفحه {page + 1} برای «{query}»:")
    for p in products:
        text = format_product(p)
        kb = product_actions_kb(p["id"], admin)
        if p.get("photo_file_id"):
            await callback.message.answer_photo(p["photo_file_id"], caption=text, parse_mode="HTML", reply_markup=kb)
        else:
            await callback.message.answer(text, parse_mode="HTML", reply_markup=kb)

    await callback.message.answer(
        "ناوبری:",
        reply_markup=pagination_kb(query, page, total, PAGE_SIZE)
    )
    await callback.answer()


# ---------- استعلام تصویری (Mini App) ----------
@router.message(F.text == "📷 استعلام تصویری")
async def image_search_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "برای اسکن بارکد روی دکمه زیر بزنید.\n"
        "دوربین باز می‌شود و بارکد را اسکن کنید.",
        reply_markup=barcode_webapp_kb()
    )


@router.message(F.content_type == ContentType.WEB_APP_DATA)
async def webapp_data_handler(message: Message):
    """دریافت بارکد اسکن‌شده از مینی‌اپ"""
    data = message.web_app_data.data
    barcode = data.strip() if data else ""
    if not barcode:
        await message.answer("بارکدی دریافت نشد.")
        return

    product = await get_product_by_barcode(barcode)
    admin = is_admin(message.from_user)

    if not product:
        await message.answer(
            f"❌ کالایی با بارکد <code>{barcode}</code> پیدا نشد.",
            parse_mode="HTML",
            reply_markup=main_menu(admin)
        )
        return

    text = format_product(product)
    kb = product_actions_kb(product["id"], admin)
    if product.get("photo_file_id"):
        await message.answer_photo(
            product["photo_file_id"],
            caption=text,
            parse_mode="HTML",
            reply_markup=kb
        )
    else:
        await message.answer(text, parse_mode="HTML", reply_markup=kb)

    await message.answer("منوی اصلی:", reply_markup=main_menu(admin))