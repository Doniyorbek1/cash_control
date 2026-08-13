from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database.models import Category, Transaction, TransactionType
from utils.states import AddExpenseState
from keyboards.inline_kb import get_categories_keyboard, get_confirmation_keyboard

finance_router = Router()

@finance_router.message(F.text == "💸 Xarajat qo'shish")
async def start_expense(message: Message, state: FSMContext, db_session: AsyncSession):
    stmt = select(Category).where(Category.user_id == message.from_user.id)
    res = await db_session.execute(stmt)
    categories = res.scalars().all()
    
    await state.set_state(AddExpenseState.select_category)
    await message.answer(
        "Xarajat kategoriyasini tanlang:",
        reply_markup=get_categories_keyboard(categories)
    )

@finance_router.callback_query(AddExpenseState.select_category, F.data.startswith("cat_"))
async def process_category_selection(callback: CallbackQuery, state: FSMContext):
    cat_id = int(callback.data.split("_")[1])
    await state.update_data(selected_category_id=cat_id)
    
    await state.set_state(AddExpenseState.enter_amount)
    await callback.message.edit_text("Xarajat summasini kiriting (masalan: 35000 yoki 35000.50):")
    await callback.answer()

@finance_router.message(AddExpenseState.enter_amount)
async def process_amount(message: Message, state: FSMContext, db_session: AsyncSession):
    try:
        amount_text = message.text.replace(" ", "").replace(",", ".")
        amount = float(amount_text)
        if amount <= 0:
            raise ValueError()
    except ValueError:
        await message.answer("⚠️ Iltimos, to'g'ri musbat son kiriting (masalan: 45000):")
        return

    # Summani va kategoriya nomini saqlab, tasdiqlash bosqichiga o'tkazish
    data = await state.get_data()
    category_id = data["selected_category_id"]
    cat = await db_session.get(Category, category_id)

    await state.update_data(
        amount=amount, 
        category_name=cat.name if cat else 'Noma’lum'
    )
    
    await state.set_state(AddExpenseState.confirm)

    confirm_text = (
        f"<b>⚠️ Ma’lumotlarni tasdiqlang:</b>\n\n"
        f"<b>Kategoriya:</b> {cat.name if cat else 'Noma’lum'}\n"
        f"<b>Summa:</b> {amount:,.2f} so'm\n\n"
        f"Ushbu xarajat saqlansinmi?"
    )

    await message.answer(
        confirm_text,
        parse_mode="HTML",
        reply_markup=get_confirmation_keyboard()
    )

@finance_router.callback_query(AddExpenseState.confirm, F.data == "confirm_expense")
async def confirm_and_save_expense(callback: CallbackQuery, state: FSMContext, db_session: AsyncSession):
    data = await state.get_data()
    
    # Bazaga saqlash jarayoni
    transaction = Transaction(
        user_id=callback.from_user.id,
        category_id=data["selected_category_id"],
        amount=data["amount"],
        type=TransactionType.EXPENSE
    )
    db_session.add(transaction)
    await db_session.commit()

    await state.clear()
    await callback.message.edit_text(
        f"✅ <b>Xarajat muvaffaqiyatli saqlandi!</b>\n\n"
        f"<b>Kategoriya:</b> {data['category_name']}\n"
        f"<b>Summa:</b> {data['amount']:,.2f} so'm",
        parse_mode="HTML"
    )
    await callback.answer()

@finance_router.callback_query(F.data == "cancel_action")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Amal bekor qilindi.")
    await callback.answer()