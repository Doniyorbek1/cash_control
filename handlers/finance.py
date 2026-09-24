from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from database.models import Category, Transaction, TransactionType
from utils.states import AddExpenseState, AddIncomeState
from keyboards.inline_kb import (
    get_categories_keyboard,
    get_confirmation_keyboard,
    get_skip_description_keyboard
)

finance_router = Router()

# Standart kategoriyalar (agar bazada bo'lmasa avtomatik tiklash uchun)
DEFAULT_EXPENSE_CATS = ["🍔 Oziq-ovqat", "🚕 Transport", "🏠 Kommunal", "🎬 O'yin-kulgi", "🛍 Xaridlar", "💊 Salomatlik"]
DEFAULT_INCOME_CATS = ["💼 Oylik maosh", "💻 Frilans / Qo'shimcha", "📈 Investitsiya", "🎁 Sovg'a", "🔄 Boshqa kirim"]

# ==================== 1. XARAJAT QO'SHISH ====================

@finance_router.message(F.text == "💸 Xarajat qo'shish")
async def start_expense(message: Message, state: FSMContext, db_session: AsyncSession):
    stmt = select(Category).where(
        Category.user_id == message.from_user.id,
        (Category.type == TransactionType.EXPENSE) | (Category.type.is_(None))
    )
    res = await db_session.execute(stmt)
    categories = res.scalars().all()
    
    # Agar foydalanuvchida xarajat kategoriyalari bo'lmasa, avtomatik qo'shish
    if not categories:
        for cat_name in DEFAULT_EXPENSE_CATS:
            db_session.add(Category(user_id=message.from_user.id, name=cat_name, type=TransactionType.EXPENSE, is_default=True))
        await db_session.commit()
        res = await db_session.execute(stmt)
        categories = res.scalars().all()

    await state.set_state(AddExpenseState.select_category)
    await message.answer(
        "<b>💸 Xarajat kategoriyasini tanlang:</b>",
        parse_mode="HTML",
        reply_markup=get_categories_keyboard(categories, prefix="exp_cat")
    )

@finance_router.callback_query(AddExpenseState.select_category, F.data.startswith("exp_cat_"))
async def process_expense_category(callback: CallbackQuery, state: FSMContext, db_session: AsyncSession):
    cat_id = int(callback.data.split("_")[2])
    cat = await db_session.get(Category, cat_id)
    await state.update_data(selected_category_id=cat_id, category_name=cat.name if cat else "Noma'lum")
    
    await state.set_state(AddExpenseState.enter_amount)
    await callback.message.edit_text("<b>Xarajat summasini kiriting</b> (masalan: <code>35000</code>):", parse_mode="HTML")
    await callback.answer()

@finance_router.message(AddExpenseState.enter_amount)
async def process_expense_amount(message: Message, state: FSMContext):
    try:
        amount_text = message.text.replace(" ", "").replace(",", ".")
        amount = float(amount_text)
        if amount <= 0:
            raise ValueError()
    except ValueError:
        await message.answer("⚠️ Iltimos, to'g'ri musbat son kiriting (masalan: <code>45000</code>):", parse_mode="HTML")
        return

    await state.update_data(amount=amount)
    await state.set_state(AddExpenseState.enter_description)
    await message.answer(
        "Ushbu xarajat uchun <b>izoh kiriting</b> (masalan: <i>Tushlik</i>) yoki izohsiz davom eting:",
        parse_mode="HTML",
        reply_markup=get_skip_description_keyboard(skip_callback="skip_expense_desc")
    )

@finance_router.callback_query(AddExpenseState.enter_description, F.data == "skip_expense_desc")
async def skip_expense_description(callback: CallbackQuery, state: FSMContext):
    await state.update_data(description=None)
    await show_expense_confirmation(callback.message, state, is_callback=True)
    await callback.answer()

@finance_router.message(AddExpenseState.enter_description)
async def process_expense_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text.strip())
    await show_expense_confirmation(message, state, is_callback=False)

async def show_expense_confirmation(target_message: Message, state: FSMContext, is_callback: bool = False):
    data = await state.get_data()
    await state.set_state(AddExpenseState.confirm)
    
    desc_text = data.get("description") or "Mavjud emas"
    confirm_text = (
        f"<b>⚠️ Xarajat ma’lumotlarini tasdiqlang:</b>\n\n"
        f"📁 <b>Kategoriya:</b> {data.get('category_name')}\n"
        f"💸 <b>Summa:</b> {data.get('amount'):,.2f} so'm\n"
        f"📝 <b>Izoh:</b> {desc_text}\n\n"
        f"Ushbu xarajat saqlansinmi?"
    )
    if is_callback:
        await target_message.edit_text(confirm_text, parse_mode="HTML", reply_markup=get_confirmation_keyboard("confirm_expense"))
    else:
        await target_message.answer(confirm_text, parse_mode="HTML", reply_markup=get_confirmation_keyboard("confirm_expense"))

@finance_router.callback_query(AddExpenseState.confirm, F.data == "confirm_expense")
async def confirm_and_save_expense(callback: CallbackQuery, state: FSMContext, db_session: AsyncSession):
    data = await state.get_data()
    
    transaction = Transaction(
        user_id=callback.from_user.id,
        category_id=data["selected_category_id"],
        amount=data["amount"],
        type=TransactionType.EXPENSE,
        description=data.get("description")
    )
    db_session.add(transaction)
    await db_session.commit()
    
    await state.clear()
    desc_str = f"\n📝 <b>Izoh:</b> {data.get('description')}" if data.get("description") else ""
    await callback.message.edit_text(
        f"✅ <b>Xarajat muvaffaqiyatli saqlandi!</b>\n\n"
        f"📁 <b>Kategoriya:</b> {data['category_name']}\n"
        f"💸 <b>Summa:</b> {data['amount']:,.2f} so'm{desc_str}",
        parse_mode="HTML"
    )
    await callback.answer()


# ==================== 2. KIRIM QO'SHISH ====================

@finance_router.message(F.text == "💰 Kirim qo'shish")
async def start_income(message: Message, state: FSMContext, db_session: AsyncSession):
    stmt = select(Category).where(
        Category.user_id == message.from_user.id,
        Category.type == TransactionType.INCOME
    )
    res = await db_session.execute(stmt)
    categories = res.scalars().all()
    
    # Agar foydalanuvchida daromad kategoriyalari bo'lmasa, avtomatik qo'shish
    if not categories:
        for cat_name in DEFAULT_INCOME_CATS:
            db_session.add(Category(user_id=message.from_user.id, name=cat_name, type=TransactionType.INCOME, is_default=True))
        await db_session.commit()
        res = await db_session.execute(stmt)
        categories = res.scalars().all()

    await state.set_state(AddIncomeState.select_category)
    await message.answer(
        "<b>💰 Daromad (kirim) kategoriyasini tanlang:</b>",
        parse_mode="HTML",
        reply_markup=get_categories_keyboard(categories, prefix="inc_cat")
    )

@finance_router.callback_query(AddIncomeState.select_category, F.data.startswith("inc_cat_"))
async def process_income_category(callback: CallbackQuery, state: FSMContext, db_session: AsyncSession):
    cat_id = int(callback.data.split("_")[2])
    cat = await db_session.get(Category, cat_id)
    await state.update_data(selected_category_id=cat_id, category_name=cat.name if cat else "Noma'lum")
    
    await state.set_state(AddIncomeState.enter_amount)
    await callback.message.edit_text("<b>Kirim summasini kiriting</b> (masalan: <code>2000000</code>):", parse_mode="HTML")
    await callback.answer()

@finance_router.message(AddIncomeState.enter_amount)
async def process_income_amount(message: Message, state: FSMContext):
    try:
        amount_text = message.text.replace(" ", "").replace(",", ".")
        amount = float(amount_text)
        if amount <= 0:
            raise ValueError()
    except ValueError:
        await message.answer("⚠️ Iltimos, to'g'ri musbat son kiriting (masalan: <code>500000</code>):", parse_mode="HTML")
        return

    await state.update_data(amount=amount)
    await state.set_state(AddIncomeState.enter_description)
    await message.answer(
        "Ushbu kirim uchun <b>izoh kiriting</b> (masalan: <i>Avgust oyligi</i>) yoki izohsiz davom eting:",
        parse_mode="HTML",
        reply_markup=get_skip_description_keyboard(skip_callback="skip_income_desc")
    )

@finance_router.callback_query(AddIncomeState.enter_description, F.data == "skip_income_desc")
async def skip_income_description(callback: CallbackQuery, state: FSMContext):
    await state.update_data(description=None)
    await show_income_confirmation(callback.message, state, is_callback=True)
    await callback.answer()

@finance_router.message(AddIncomeState.enter_description)
async def process_income_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text.strip())
    await show_income_confirmation(message, state, is_callback=False)

async def show_income_confirmation(target_message: Message, state: FSMContext, is_callback: bool = False):
    data = await state.get_data()
    await state.set_state(AddIncomeState.confirm)
    
    desc_text = data.get("description") or "Mavjud emas"
    confirm_text = (
        f"<b>⚠️ Kirim ma’lumotlarini tasdiqlang:</b>\n\n"
        f"📁 <b>Kategoriya:</b> {data.get('category_name')}\n"
        f"💰 <b>Summa:</b> {data.get('amount'):,.2f} so'm\n"
        f"📝 <b>Izoh:</b> {desc_text}\n\n"
        f"Ushbu kirim saqlansinmi?"
    )
    if is_callback:
        await target_message.edit_text(confirm_text, parse_mode="HTML", reply_markup=get_confirmation_keyboard("confirm_income"))
    else:
        await target_message.answer(confirm_text, parse_mode="HTML", reply_markup=get_confirmation_keyboard("confirm_income"))

@finance_router.callback_query(AddIncomeState.confirm, F.data == "confirm_income")
async def confirm_and_save_income(callback: CallbackQuery, state: FSMContext, db_session: AsyncSession):
    data = await state.get_data()
    
    transaction = Transaction(
        user_id=callback.from_user.id,
        category_id=data["selected_category_id"],
        amount=data["amount"],
        type=TransactionType.INCOME,
        description=data.get("description")
    )
    db_session.add(transaction)
    await db_session.commit()
    
    await state.clear()
    desc_str = f"\n📝 <b>Izoh:</b> {data.get('description')}" if data.get("description") else ""
    await callback.message.edit_text(
        f"✅ <b>Kirim muvaffaqiyatli saqlandi!</b>\n\n"
        f"📁 <b>Kategoriya:</b> {data['category_name']}\n"
        f"💰 <b>Summa:</b> {data['amount']:,.2f} so'm{desc_str}",
        parse_mode="HTML"
    )
    await callback.answer()


# ==================== 3. BALANS VA HISOB QOLDIG'I ====================

@finance_router.message(F.text == "💳 Balans")
async def cmd_balance(message: Message, db_session: AsyncSession):
    income_stmt = select(func.coalesce(func.sum(Transaction.amount), 0.0)).where(
        Transaction.user_id == message.from_user.id,
        Transaction.type == TransactionType.INCOME
    )
    total_income = (await db_session.execute(income_stmt)).scalar()

    expense_stmt = select(func.coalesce(func.sum(Transaction.amount), 0.0)).where(
        Transaction.user_id == message.from_user.id,
        Transaction.type == TransactionType.EXPENSE
    )
    total_expense = (await db_session.execute(expense_stmt)).scalar()

    balance = total_income - total_expense
    balance_status = "🟢 Ijobiy" if balance >= 0 else "🔴 Kamomad"

    recent_stmt = (
        select(Transaction, Category.name)
        .outerjoin(Category, Transaction.category_id == Category.id)
        .where(Transaction.user_id == message.from_user.id)
        .order_by(Transaction.created_at.desc())
        .limit(5)
    )
    recent_transactions = (await db_session.execute(recent_stmt)).all()

    text = (
        f"<b>💳 Moliyaviy Balans Holati:</b>\n\n"
        f"💰 <b>Jami Kirim:</b> +{total_income:,.2f} so'm\n"
        f"💸 <b>Jami Chiqim:</b> -{total_expense:,.2f} so'm\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💵 <b>Qoldiq (Balans):</b> <b>{balance:,.2f} so'm</b> ({balance_status})\n\n"
    )

    if recent_transactions:
        text += "<b>🕒 Oxirgi 5 ta amaliyot:</b>\n"
        for t, cat_name in recent_transactions:
            sign = "🟢 +" if t.type == TransactionType.INCOME else "🔴 -"
            cat_display = cat_name if cat_name else "Noma'lum"
            desc_display = f" (<i>{t.description}</i>)" if t.description else ""
            date_display = t.created_at.strftime("%d.%m %H:%M")
            text += f"• {sign}{t.amount:,.0f} so'm | {cat_display}{desc_display} [<code>{date_display}</code>]\n"
    else:
        text += "<i>Hozircha hech qanday amaliyot qayd etilmagan.</i>"

    await message.answer(text, parse_mode="HTML")


# ==================== BEKOR QILISH ====================

@finance_router.callback_query(F.data == "cancel_action")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Amal bekor qilindi.")
    await callback.answer()