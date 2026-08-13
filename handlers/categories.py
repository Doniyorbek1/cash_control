from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database.models import Category
from utils.states import AddCategoryState
from keyboards.inline_kb import get_settings_keyboard

category_router = Router()

@category_router.message(F.text == "⚙️ Sozlamalar (Kategoriyalar)")
async def cmd_settings(message: Message):
    await message.answer(
        "<b>Kategoriyalarni boshqarish bo'limi:</b>\n\n"
        "Mavjud kategoriyalarni ko'rishingiz yoki yangisini qo'shishingiz mumkin.",
        parse_mode="HTML",
        reply_markup=get_settings_keyboard()
    )

@category_router.callback_query(F.data == "list_categories")
async def list_user_categories(callback: CallbackQuery, db_session: AsyncSession):
    stmt = select(Category).where(Category.user_id == callback.from_user.id)
    res = await db_session.execute(stmt)
    categories = res.scalars().all()
    
    text = "<b>Sizning kategoriyalaringiz:</b>\n\n"
    for cat in categories:
        cat_type = "(standart)" if cat.is_default else "(shaxsiy)"
        text += f"• {cat.name} <i>{cat_type}</i>\n"
        
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_settings_keyboard())
    await callback.answer()

@category_router.callback_query(F.data == "add_custom_category")
async def start_add_category(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddCategoryState.enter_name)
    await callback.message.answer("Yangi kategoriya nomini kiriting (masalan: 🚗 Avto-xizmat):")
    await callback.answer()

@category_router.message(AddCategoryState.enter_name)
async def process_category_name(message: Message, state: FSMContext, db_session: AsyncSession):
    cat_name = message.text.strip()
    
    new_cat = Category(
        user_id=message.from_user.id,
        name=cat_name,
        is_default=False
    )
    db_session.add(new_cat)
    await db_session.commit()
    
    await state.clear()
    await message.answer(f"✅ <b>{cat_name}</b> kategoriyasi muvaffaqiyatli qo'shildi!", parse_mode="HTML")