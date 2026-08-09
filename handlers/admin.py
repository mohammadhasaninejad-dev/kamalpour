from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ContentType
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
import openpyxl
import tempfile
import os

import inspect

from states import AddProduct, EditProduct, DeleteProduct, ImportExcel
from keyboards import (
    admin_menu, main_menu, cancel_kb, skip_kb,
    confirm_delete_kb, product_actions_kb, back_to_admin_kb, edit_fields_kb
)
from database import (
    add_product, update_product, delete_product, get_product,
    get_all_products, count_products, build_product_name, get_product_by_name
)
from utils import is_admin, format_product, format_price

router = Router()


def admin_only(handler):
    """
    دکوریتور یکپارچه برای گیت‌کردن هندلرهای ادمین.
    قبلاً این تابع تعریف شده بود ولی هیچ‌جا استفاده نمی‌شد و به‌جایش هر هندلر
    جداگانه و دستی is_admin را چک می‌کرد؛ اگر هندلر جدیدی اضافه می‌شد و این چک
    فراموش می‌شد یک حفره‌ی امنیتی ایجاد می‌کرد. حالا همه‌جا از همین دکوریتور
    استفاده می‌شود.

    نکته‌ی فنی: چون wrapper خودش **kwargs دارد، aiogram همه‌ی چیزهایی که در دسترس
    است (state, bot, dispatcher, ...) را به آن پاس می‌دهد. اگر همه‌ی این‌ها را
    بی‌قید و شرط به handler اصلی فوروارد کنیم، برای هندلرهایی که فقط message
    یا (message, state) می‌گیرند خطای "unexpected keyword argument" می‌دهد.
    برای همین با inspect فقط پارامترهایی که خودِ handler واقعاً در امضایش
    اعلام کرده فیلتر و فوروارد می‌شوند.
    """
    handler_params = inspect.signature(handler).parameters

    async def wrapper(event, **kwargs):
        user = event.from_user if hasattr(event, "from_user") else None
        if not is_admin(user):
            if isinstance(event, Message):
                await event.answer("⛔ دسترسی فقط برای ادمین.")
            elif isinstance(event, CallbackQuery):
                await event.answer("⛔ دسترسی فقط برای ادمین.", show_alert=True)
            return
        accepted = {k: v for k, v in kwargs.items() if k in handler_params}
        return await handler(event, **accepted)
    return wrapper


# ---------- منوی مدیریت ----------
@router.message(F.text == "📦 مدیریت کالا")
@admin_only
async def admin_panel(message: Message, state: FSMContext):
    await state.clear()
    total = await count_products()
    await message.answer(
        f"پنل مدیریت کالا\nتعداد کل کالاها: {total}",
        reply_markup=admin_menu()
    )


@router.message(F.text == "🔙 بازگشت به مدیریت کالا")
@admin_only
async def back_to_admin(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("پنل مدیریت:", reply_markup=admin_menu())


# ---------- افزودن کالا ----------
@router.message(F.text == "➕ افزودن کالا")
@admin_only
async def add_start(message: Message, state: FSMContext):
    await state.set_state(AddProduct.category)
    await message.answer("دسته کالا را وارد کنید (مثال: دفتر):", reply_markup=cancel_kb())


@router.message(AddProduct.category, F.text == "❌ انصراف")
@router.message(AddProduct.attr1, F.text == "❌ انصراف")
@router.message(AddProduct.attr2, F.text == "❌ انصراف")
@router.message(AddProduct.attr3, F.text == "❌ انصراف")
@router.message(AddProduct.attr4, F.text == "❌ انصراف")
@router.message(AddProduct.attr5, F.text == "❌ انصراف")
@router.message(AddProduct.brand, F.text == "❌ انصراف")
@router.message(AddProduct.purchase_price, F.text == "❌ انصراف")
@router.message(AddProduct.sale_price, F.text == "❌ انصراف")
@router.message(AddProduct.wholesale_price, F.text == "❌ انصراف")
@router.message(AddProduct.stock, F.text == "❌ انصراف")
@router.message(AddProduct.barcode, F.text == "❌ انصراف")
@router.message(AddProduct.seller_name, F.text == "❌ انصراف")
@router.message(AddProduct.seller_code, F.text == "❌ انصراف")
@router.message(AddProduct.photo, F.text == "❌ انصراف")
async def add_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("افزودن کالا لغو شد.", reply_markup=admin_menu())


@router.message(AddProduct.category)
async def add_category(message: Message, state: FSMContext):
    await state.update_data(category=message.text.strip())
    await state.set_state(AddProduct.attr1)
    await message.answer("خصوصیت ۱ را وارد کنید (یا رد کردن):", reply_markup=skip_kb())


@router.message(AddProduct.attr1)
async def add_attr1(message: Message, state: FSMContext):
    val = None if message.text == "⏭ رد کردن" else message.text.strip()
    await state.update_data(attr1=val)
    await state.set_state(AddProduct.attr2)
    await message.answer("خصوصیت ۲:", reply_markup=skip_kb())


@router.message(AddProduct.attr2)
async def add_attr2(message: Message, state: FSMContext):
    val = None if message.text == "⏭ رد کردن" else message.text.strip()
    await state.update_data(attr2=val)
    await state.set_state(AddProduct.attr3)
    await message.answer("خصوصیت ۳:", reply_markup=skip_kb())


@router.message(AddProduct.attr3)
async def add_attr3(message: Message, state: FSMContext):
    val = None if message.text == "⏭ رد کردن" else message.text.strip()
    await state.update_data(attr3=val)
    await state.set_state(AddProduct.attr4)
    await message.answer("خصوصیت ۴:", reply_markup=skip_kb())


@router.message(AddProduct.attr4)
async def add_attr4(message: Message, state: FSMContext):
    val = None if message.text == "⏭ رد کردن" else message.text.strip()
    await state.update_data(attr4=val)
    await state.set_state(AddProduct.attr5)
    await message.answer("خصوصیت ۵:", reply_markup=skip_kb())


@router.message(AddProduct.attr5)
async def add_attr5(message: Message, state: FSMContext):
    val = None if message.text == "⏭ رد کردن" else message.text.strip()
    await state.update_data(attr5=val)
    await state.set_state(AddProduct.brand)
    await message.answer("برند:", reply_markup=skip_kb())


@router.message(AddProduct.brand)
async def add_brand(message: Message, state: FSMContext):
    val = None if message.text == "⏭ رد کردن" else message.text.strip()
    await state.update_data(brand=val)
    await state.set_state(AddProduct.purchase_price)
    await message.answer("قیمت خرید (تومان) - عدد وارد کنید یا رد کنید:", reply_markup=skip_kb())


def parse_number(text: str):
    if text == "⏭ رد کردن":
        return 0
    try:
        return float(text.replace(",", "").replace("٬", "").strip())
    except Exception:
        return None


@router.message(AddProduct.purchase_price)
async def add_purchase(message: Message, state: FSMContext):
    val = parse_number(message.text)
    if val is None:
        await message.answer("عدد معتبر وارد کنید یا رد کنید.")
        return
    await state.update_data(purchase_price=val)
    await state.set_state(AddProduct.sale_price)
    await message.answer("قیمت فروش واحد (تومان):", reply_markup=skip_kb())


@router.message(AddProduct.sale_price)
async def add_sale(message: Message, state: FSMContext):
    val = parse_number(message.text)
    if val is None:
        await message.answer("عدد معتبر وارد کنید یا رد کنید.")
        return
    await state.update_data(sale_price=val)
    await state.set_state(AddProduct.wholesale_price)
    await message.answer("قیمت فروش عمده (تومان):", reply_markup=skip_kb())


@router.message(AddProduct.wholesale_price)
async def add_wholesale(message: Message, state: FSMContext):
    val = parse_number(message.text)
    if val is None:
        await message.answer("عدد معتبر وارد کنید یا رد کنید.")
        return
    await state.update_data(wholesale_price=val)
    await state.set_state(AddProduct.stock)
    await message.answer("موجودی (عدد صحیح):", reply_markup=skip_kb())


@router.message(AddProduct.stock)
async def add_stock(message: Message, state: FSMContext):
    if message.text == "⏭ رد کردن":
        val = 0
    else:
        try:
            val = int(message.text.strip())
        except Exception:
            await message.answer("عدد صحیح وارد کنید یا رد کنید.")
            return
    await state.update_data(stock=val)
    await state.set_state(AddProduct.barcode)
    await message.answer("بارکد کالا:", reply_markup=skip_kb())


@router.message(AddProduct.barcode)
async def add_barcode(message: Message, state: FSMContext):
    val = None if message.text == "⏭ رد کردن" else message.text.strip()
    await state.update_data(barcode=val)
    await state.set_state(AddProduct.seller_name)
    await message.answer("نام فروشنده:", reply_markup=skip_kb())


@router.message(AddProduct.seller_name)
async def add_seller_name(message: Message, state: FSMContext):
    val = None if message.text == "⏭ رد کردن" else message.text.strip()
    await state.update_data(seller_name=val)
    await state.set_state(AddProduct.seller_code)
    await message.answer("کد فروشنده:", reply_markup=skip_kb())


@router.message(AddProduct.seller_code)
async def add_seller_code(message: Message, state: FSMContext):
    val = None if message.text == "⏭ رد کردن" else message.text.strip()
    await state.update_data(seller_code=val)
    await state.set_state(AddProduct.photo)
    await message.answer(
        "عکس کالا را ارسال کنید (یا رد کردن):",
        reply_markup=skip_kb()
    )


@router.message(AddProduct.photo, F.photo)
async def add_photo(message: Message, state: FSMContext):
    file_id = message.photo[-1].file_id
    data = await state.get_data()
    data["photo_file_id"] = file_id
    product_id = await add_product(data)
    await state.clear()
    product = await get_product(product_id)
    await message.answer("✅ کالا با موفقیت اضافه شد:", reply_markup=admin_menu())
    await message.answer(format_product(product), parse_mode="HTML")


@router.message(AddProduct.photo)
async def add_photo_skip(message: Message, state: FSMContext):
    if message.text != "⏭ رد کردن":
        await message.answer("عکس بفرستید یا رد کنید.")
        return
    data = await state.get_data()
    data["photo_file_id"] = None
    product_id = await add_product(data)
    await state.clear()
    product = await get_product(product_id)
    await message.answer("✅ کالا با موفقیت اضافه شد (بدون عکس):", reply_markup=admin_menu())
    await message.answer(format_product(product), parse_mode="HTML")


# ---------- ویرایش کالا ----------
FIELD_FA_NAMES = {
    "category": "دسته",
    "attr1": "خصوصیت ۱",
    "attr2": "خصوصیت ۲",
    "attr3": "خصوصیت ۳",
    "attr4": "خصوصیت ۴",
    "attr5": "خصوصیت ۵",
    "brand": "برند",
    "purchase_price": "قیمت خرید",
    "sale_price": "قیمت فروش",
    "wholesale_price": "قیمت عمده",
    "stock": "موجودی",
    "barcode": "بارکد",
    "seller_name": "فروشنده",
    "seller_code": "کد فروشنده",
    "photo_file_id": "عکس",
}


@router.message(F.text == "✏️ ویرایش کالا")
@admin_only
async def edit_start(message: Message, state: FSMContext):
    await state.set_state(EditProduct.waiting_id)
    await message.answer(
        "شناسه (ID) کالایی که می‌خواهید ویرایش کنید را وارد کنید:\n"
        "(از لیست کالاها یا استعلام می‌توانید ID را ببینید)",
        reply_markup=cancel_kb()
    )


@router.message(EditProduct.waiting_id, F.text == "❌ انصراف")
async def edit_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("لغو شد.", reply_markup=admin_menu())


@router.message(EditProduct.waiting_id)
async def edit_id(message: Message, state: FSMContext):
    try:
        pid = int(message.text.strip())
    except Exception:
        await message.answer("شناسه عددی وارد کنید.")
        return
    product = await get_product(pid)
    if not product:
        await message.answer("کالایی با این شناسه پیدا نشد.")
        return
    await state.clear()
    await message.answer(format_product(product), parse_mode="HTML")
    await message.answer(
        "کدام فیلد را می‌خواهید تغییر دهید؟",
        reply_markup=edit_fields_kb(pid)
    )


@router.callback_query(F.data.startswith("edit:"))
@admin_only
async def inline_edit_start(callback: CallbackQuery, state: FSMContext):
    """وقتی از دکمه ویرایش زیر محصول زده می‌شود"""
    pid = int(callback.data.split(":")[1])
    product = await get_product(pid)
    if not product:
        await callback.answer("کالا پیدا نشد", show_alert=True)
        return
    await state.clear()
    await callback.message.answer(format_product(product), parse_mode="HTML")
    await callback.message.answer(
        "کدام فیلد را می‌خواهید تغییر دهید؟",
        reply_markup=edit_fields_kb(pid)
    )
    await callback.answer()


@router.callback_query(F.data == "cancel_edit")
async def cancel_edit_cb(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("ویرایش لغو شد.")
    await callback.answer()


@router.callback_query(F.data.startswith("efield:"))
@admin_only
async def edit_field_chosen(callback: CallbackQuery, state: FSMContext):
    try:
        _, pid_str, field = callback.data.split(":", 2)
        pid = int(pid_str)
    except Exception:
        await callback.answer("خطا", show_alert=True)
        return

    await state.update_data(edit_id=pid, edit_field=field)
    fa_name = FIELD_FA_NAMES.get(field, field)

    if field == "photo_file_id":
        await callback.message.answer(
            f"🖼 عکس جدید برای «{fa_name}» را ارسال کنید:",
            reply_markup=cancel_kb()
        )
    else:
        await callback.message.answer(
            f"مقدار جدید برای «{fa_name}» را وارد کنید:",
            reply_markup=cancel_kb()
        )
    await state.set_state(EditProduct.value)
    await callback.answer()


@router.message(EditProduct.value, F.text == "❌ انصراف")
async def edit_value_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("لغو شد.", reply_markup=admin_menu())


@router.message(EditProduct.value, F.photo)
async def edit_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    if data.get("edit_field") != "photo_file_id":
        await message.answer("الان منتظر متن هستم.")
        return
    pid = data["edit_id"]
    product = await get_product(pid)
    if not product:
        await state.clear()
        await message.answer("کالا پیدا نشد.", reply_markup=admin_menu())
        return
    product["photo_file_id"] = message.photo[-1].file_id
    await update_product(pid, product)
    await state.clear()
    await message.answer("✅ عکس به‌روز شد.", reply_markup=admin_menu())
    await message.answer_photo(product["photo_file_id"], caption=format_product(product), parse_mode="HTML")


@router.message(EditProduct.value)
async def edit_value(message: Message, state: FSMContext):
    data = await state.get_data()
    field = data.get("edit_field")
    pid = data["edit_id"]
    product = await get_product(pid)
    if not product:
        await state.clear()
        await message.answer("کالا پیدا نشد.", reply_markup=admin_menu())
        return

    text = message.text.strip()
    if field in ("purchase_price", "sale_price", "wholesale_price"):
        val = parse_number(text)
        if val is None:
            await message.answer("عدد معتبر وارد کنید.")
            return
        product[field] = val
    elif field == "stock":
        try:
            product[field] = int(text)
        except Exception:
            await message.answer("عدد صحیح وارد کنید.")
            return
    else:
        product[field] = text

    await update_product(pid, product)
    await state.clear()
    updated = await get_product(pid)
    await message.answer("✅ کالا به‌روز شد:", reply_markup=admin_menu())
    await message.answer(format_product(updated), parse_mode="HTML")


# ---------- حذف کالا ----------
@router.message(F.text == "🗑 حذف کالا")
@admin_only
async def delete_start(message: Message, state: FSMContext):
    await state.set_state(DeleteProduct.waiting_id)
    await message.answer("شناسه کالایی که می‌خواهید حذف کنید را وارد کنید:", reply_markup=cancel_kb())


@router.message(DeleteProduct.waiting_id, F.text == "❌ انصراف")
async def delete_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("لغو شد.", reply_markup=admin_menu())


@router.message(DeleteProduct.waiting_id)
async def delete_id(message: Message, state: FSMContext):
    try:
        pid = int(message.text.strip())
    except Exception:
        await message.answer("شناسه عددی وارد کنید.")
        return
    product = await get_product(pid)
    if not product:
        await message.answer("کالایی پیدا نشد.")
        return
    await state.clear()
    await message.answer(
        f"آیا مطمئن هستید که می‌خواهید این کالا را حذف کنید؟\n\n{format_product(product)}",
        parse_mode="HTML",
        reply_markup=confirm_delete_kb(pid)
    )


@router.callback_query(F.data.startswith("confirm_del:"))
@admin_only
async def confirm_delete(callback: CallbackQuery):
    pid = int(callback.data.split(":")[1])
    await delete_product(pid)
    await callback.message.edit_text("✅ کالا حذف شد.")
    await callback.answer()


@router.callback_query(F.data == "cancel_del")
async def cancel_delete(callback: CallbackQuery):
    await callback.message.edit_text("حذف لغو شد.")
    await callback.answer()


@router.callback_query(F.data.startswith("del:"))
@admin_only
async def inline_delete(callback: CallbackQuery):
    pid = int(callback.data.split(":")[1])
    product = await get_product(pid)
    if not product:
        await callback.answer("پیدا نشد", show_alert=True)
        return
    await callback.message.answer(
        f"حذف این کالا؟\n\n{format_product(product)}",
        parse_mode="HTML",
        reply_markup=confirm_delete_kb(pid)
    )
    await callback.answer()


# ---------- لیست کالاها ----------
@router.message(F.text == "📋 لیست کالاها")
@admin_only
async def list_products(message: Message):
    total = await count_products()
    products = await get_all_products(offset=0, limit=15)
    if not products:
        await message.answer("هنوز کالایی ثبت نشده.")
        return
    lines = [f"📋 آخرین کالاها (از {total} کالا):\n"]
    for p in products:
        lines.append(f"🆔 {p['id']} | {p.get('name') or '—'}")
    await message.answer("\n".join(lines), reply_markup=admin_menu())


# ---------- ایمپورت اکسل ----------
@router.message(F.text == "📥 ایمپورت اکسل")
@admin_only
async def import_start(message: Message, state: FSMContext):
    await state.set_state(ImportExcel.waiting_file)
    await message.answer(
        "فایل اکسل را ارسال کنید.\n"
        "✅ این عملیات جایگزین‌کننده (destructive) نیست: کالاهایی که از قبل با همین "
        "دسته/خصوصیت/برند وجود داشته باشند فقط قیمت‌شان به‌روزرسانی می‌شود و بارکد، "
        "موجودی و عکسی که قبلاً برایشان ثبت کرده‌اید دست‌نخورده می‌ماند. کالاهای جدیدِ "
        "اکسل هم اضافه می‌شوند.\n"
        "ستون‌ها باید مطابق نمونه قبلی باشند.",
        reply_markup=cancel_kb()
    )


@router.message(ImportExcel.waiting_file, F.text == "❌ انصراف")
async def import_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("لغو شد.", reply_markup=admin_menu())


@router.message(ImportExcel.waiting_file, F.document)
async def import_excel(message: Message, state: FSMContext):
    doc = message.document
    if not doc.file_name.endswith((".xlsx", ".xls")):
        await message.answer("فقط فایل اکسل (.xlsx) بفرستید.")
        return

    await message.answer("در حال پردازش فایل... لطفاً صبر کنید.")
    file = await message.bot.get_file(doc.file_id)
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        await message.bot.download_file(file.file_path, tmp.name)
        tmp_path = tmp.name

    try:
        wb = openpyxl.load_workbook(tmp_path)
        ws = wb.active

        # پیدا کردن ردیف هدر
        header_row = None
        for row in range(1, 6):
            vals = [ws.cell(row, c).value for c in range(1, 15)]
            if any(v and "دسته" in str(v) for v in vals):
                header_row = row
                break
        if not header_row:
            await message.answer("هدر «دسته» در فایل پیدا نشد.")
            return

        # پیدا کردن ستون‌ها
        col_map = {}
        for c in range(1, 20):
            val = ws.cell(header_row, c).value
            if not val:
                continue
            v = str(val).strip()
            if "دسته" in v:
                col_map["category"] = c
            elif "خصوصیت 1" in v or "خصوصیت۱" in v:
                col_map["attr1"] = c
            elif "خصوصیت 2" in v or "خصوصیت۲" in v:
                col_map["attr2"] = c
            elif "خصوصیت 3" in v or "خصوصیت۳" in v:
                col_map["attr3"] = c
            elif "خصوصیت 4" in v or "خصوصیت۴" in v:
                col_map["attr4"] = c
            elif "خصوصیت 5" in v or "خصوصیت۵" in v:
                col_map["attr5"] = c
            elif "برند" in v:
                col_map["brand"] = c
            elif "قیمت خرید" in v:
                col_map["purchase_price"] = c
            elif "فروش واحد تک" in v or "قیمت فروش واحد تک" in v:
                col_map["sale_price"] = c
            elif "عمده" in v:
                col_map["wholesale_price"] = c
            elif "فروشنده" in v and "کد" not in v:
                col_map["seller_name"] = c
            elif "کد فروشنده" in v:
                col_map["seller_code"] = c
            elif "بارکد" in v:
                col_map["barcode"] = c
            elif "موجودی" in v:
                col_map["stock"] = c

        if "category" not in col_map:
            await message.answer("ستون دسته پیدا نشد.")
            return

        added, updated = 0, 0
        for row in range(header_row + 1, ws.max_row + 1):
            cat = ws.cell(row, col_map["category"]).value
            if not cat or not str(cat).strip():
                continue

            def get(col_key):
                c = col_map.get(col_key)
                if not c:
                    return None
                v = ws.cell(row, c).value
                return v if v is not None and str(v).strip() != "" else None

            def get_num(col_key):
                v = get(col_key)
                if v is None:
                    return None
                try:
                    return float(v)
                except Exception:
                    return None

            def get_int(col_key):
                v = get(col_key)
                if v is None:
                    return None
                try:
                    return int(float(v))
                except Exception:
                    return None

            data = {
                "category": str(get("category")).strip() if get("category") else None,
                "attr1": str(get("attr1")).strip() if get("attr1") else None,
                "attr2": str(get("attr2")).strip() if get("attr2") else None,
                "attr3": str(get("attr3")).strip() if get("attr3") else None,
                "attr4": str(get("attr4")).strip() if get("attr4") else None,
                "attr5": str(get("attr5")).strip() if get("attr5") else None,
                "brand": str(get("brand")).strip() if get("brand") else None,
                "purchase_price": get_num("purchase_price") or 0,
                "sale_price": get_num("sale_price") or 0,
                "wholesale_price": get_num("wholesale_price") or 0,
                "seller_name": str(get("seller_name")).strip() if get("seller_name") else None,
                "seller_code": str(get("seller_code")).strip() if get("seller_code") else None,
            }

            name = build_product_name(
                data["category"], data["attr1"], data["attr2"],
                data["attr3"], data["attr4"], data["attr5"], data["brand"]
            )
            existing = await get_product_by_name(name)

            # بارکد و موجودی: اگر ستونش در اکسل بود همان مقدار اکسل استفاده می‌شود،
            # وگرنه مقدار قبلیِ ثبت‌شده در ربات (اگر کالا از قبل وجود داشت) حفظ می‌شود.
            excel_barcode = get("barcode")
            excel_stock = get_int("stock")

            if existing:
                data["barcode"] = excel_barcode if excel_barcode is not None else existing.get("barcode")
                data["stock"] = excel_stock if excel_stock is not None else existing.get("stock")
                data["photo_file_id"] = existing.get("photo_file_id")
                await update_product(existing["id"], data)
                updated += 1
            else:
                data["barcode"] = excel_barcode
                data["stock"] = excel_stock or 0
                data["photo_file_id"] = None
                await add_product(data)
                added += 1

        await state.clear()
        await message.answer(
            "✅ ایمپورت با موفقیت انجام شد.\n"
            f"➕ کالای جدید: {added}\n"
            f"🔄 کالای به‌روزشده (با حفظ بارکد/موجودی/عکس قبلی): {updated}",
            reply_markup=admin_menu()
        )
    except Exception as e:
        await message.answer(f"خطا در پردازش فایل: {e}")
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


@router.message(ImportExcel.waiting_file)
async def import_wrong(message: Message):
    await message.answer("لطفاً فایل اکسل ارسال کنید یا انصراف بزنید.")