from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from keyboards import main_menu
from utils import is_admin

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    admin = is_admin(message.from_user)
    text = (
        "سلام 👋\n"
        "به بات <b>لوازم‌التحریر</b> خوش آمدید.\n\n"
        "از منوی زیر یکی از گزینه‌ها را انتخاب کنید:"
    )
    await message.answer(text, reply_markup=main_menu(admin), parse_mode="HTML")


@router.message(Command("menu"))
@router.message(F.text == "🔙 بازگشت به منوی اصلی")
async def back_to_main(message: Message, state: FSMContext):
    await state.clear()
    admin = is_admin(message.from_user)
    await message.answer("منوی اصلی:", reply_markup=main_menu(admin))