from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from keyboards.default_kb import get_main_keyboard

start_router = Router()

@start_router.message(Command("start"))
async def cmd_start(message: Message):
    welcome_text = (
        f"Assalomu alaykum, <b>{message.from_user.first_name}</b>!\n\n"
        f"<b>Shaxsiy Moliya va Unumdorlik Botiga</b> xush kelibsiz.\n"
        f"Quyidagi menyu orqali xarajatlaringizni kiriting, hisobotlarni ko'ring "
        f"va kundalik rejalaringizni boshqaring."
    )
    await message.answer(welcome_text, parse_mode="HTML", reply_markup=get_main_keyboard())