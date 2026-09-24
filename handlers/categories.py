from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database.models import Category, TransactionType
from utils.states import AddCategoryState
from keyboards.inline_kb import get_settings_keyboard

category_router = Router()

def get_category_type_keyboard() -> InlineKeyboardMarkup:
    kb = [
        [
            InlineKeyboardButton(text="💸 Xarajat kategoriyasi", callback_data="type_expense"),
            InlineKeyboardButton(text="💰 Kirim kategoriyasi", callback_data="type_income")
        ],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_categories_manage_keyboard(categories: list[Category]) -> InlineKeyboardMarkup:
    buttons = []
    for cat in categories:
        cat_type = "💸" if cat.type == TransactionType.EXPENSE else "💰"
        del_btn = [
            InlineKeyboardButton(text=f"{cat_type} {cat.name}", callback_data=f"ignore_{cat.id}"),
            InlineKeyboardButton(text="🗑", callback_data=f"del_cat_{cat.id}")
        ] if not cat.is_default else [
            InlineKeyboardButton(text=f"{cat_type} {cat.name} (standart)", callback_data=f"ignore_{cat.id}")
        ]
        buttons.append(del_btn)
    buttons.append([InlineKeyboardButton(text="➕ Yangi qo'shish", callback_data="add_custom_category")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@category_router.message(F.text == "⚙️ Sozlamalar (Kategoriyalar)")
async def cmd_settings(message: Message):
    await message.answer(
        "<b>⚙️ Kategoriyalarni boshqarish bo'limi:</b>\n\n"
        "Mavjud kategoriyalarni ko'rishingiz yoki yangisini qo'shishingiz mumkin.",
        parse_mode="HTML",
        reply_markup=get_settings_keyboard()
    )

@category_router.callback_query(F.data == "list_categories")
async def list_user_categories(callback: CallbackQuery, db_session: AsyncSession):
    stmt = select(Category).where(Category.user_id == callback.from_user.id)
    res = await db_session.execute(stmt)
    categories = res.scalars().all()

    await callback.message.edit_text(
        "<b>📁 Sizning kategoriyalaringiz:</b>\n\n"
        "<i>(Shaxsiy kategoriyalaringizni 🗑 tugmasi orqali o'chirishingiz mumkin)</i>",
        parse_mode="HTML",
        reply_markup=get_categories_manage_keyboard(categories)
    )
    await callback.answer()

@category_router.callback_query(F.data.startswith("del_cat_"))
async def delete_custom_category(callback: CallbackQuery, db_session: AsyncSession):
    cat_id = int(callback.data.split("_")[2])
    cat = await db_session.get(Category, cat_id)
    if cat and cat.user_id == callback.from_user.id and not cat.is_default:
        await db_session.delete(cat)
        await db_session.commit()
        await callback.answer("Kategoriya o'chirildi!", show_alert=False)

        stmt = select(Category).where(Category.user_id == callback.from_user.id)
        res = await db_session.execute(stmt)
        categories = res.scalars().all()
        await callback.message.edit_reply_markup(reply_markup=get_categories_manage_keyboard(categories))
    else:
        await callback.answer("Ushbu kategoriyani o'chirib bo'lmaydi!", show_alert=True)

@category_router.callback_query(F.data == "add_custom_category")
async def start_add_category(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddCategoryState.select_type)
    await callback.message.answer(
        "Yangi kategoriya qaysi turga tegishli bo'lishini tanlang:",
        reply_markup=get_category_type_keyboard()
    )
    await callback.answer()

@category_router.callback_query(AddCategoryState.select_type, F.data.in_(["type_expense", "type_income"]))
async def process_category_type(callback: CallbackQuery, state: FSMContext):
    cat_type = TransactionType.EXPENSE if callback.data == "type_expense" else TransactionType.INCOME
    await state.update_data(cat_type=cat_type)
    await state.set_state(AddCategoryState.enter_name)
    await callback.message.edit_text("Yangi kategoriya nomini kiriting (masalan: <i>🚗 Avto-xizmat</i> yoki <i>💻 Bonus</i>):", parse_mode="HTML")
    await callback.answer()

@category_router.message(AddCategoryState.enter_name)
async def process_category_name(message: Message, state: FSMContext, db_session: AsyncSession):
    cat_name = message.text.strip()
    data = await state.get_data()
    cat_type = data.get("cat_type", TransactionType.EXPENSE)

    new_cat = Category(
        user_id=message.from_user.id,
        name=cat_name,
        type=cat_type,
        is_default=False
    )
    db_session.add(new_cat)
    await db_session.commit()

    await state.clear()
    type_name = "Xarajat" if cat_type == TransactionType.EXPENSE else "Kirim"
    await message.answer(
        f"✅ Yangi <b>{type_name}</b> kategoriyasi muvaffaqiyatli qo'shildi: <b>{cat_name}</b>",
        parse_mode="HTML"
    )

@category_router.callback_query(F.data.startswith("ignore_"))
async def ignore_callback(callback: CallbackQuery):
    await callback.answer()