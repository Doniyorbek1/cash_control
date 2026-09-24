from datetime import datetime
import pytz
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database.models import Reminder
from utils.states import AddReminderState
from services.scheduler import schedule_reminder
from config.config import config

reminders_router = Router()
local_tz = pytz.timezone(config.DEFAULT_TIMEZONE)

def get_reminders_keyboard(reminders: list[Reminder]) -> InlineKeyboardMarkup:
    buttons = []
    for r in reminders:
        time_str = r.remind_at.strftime("%d.%m.%Y %H:%M")
        btn_text = f"⏰ {r.text[:15]}... ({time_str})"
        buttons.append([
            InlineKeyboardButton(text=btn_text, callback_data=f"info_rem_{r.id}"),
            InlineKeyboardButton(text="🗑", callback_data=f"del_rem_{r.id}")
        ])
    buttons.append([InlineKeyboardButton(text="➕ Yangi eslatma yaratish", callback_data="add_new_reminder")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@reminders_router.message(F.text == "⏰ Eslatmalar")
async def cmd_reminders(message: Message, db_session: AsyncSession):
    stmt = select(Reminder).where(Reminder.user_id == message.from_user.id).order_by(Reminder.remind_at.asc())
    res = await db_session.execute(stmt)
    reminders = res.scalars().all()

    text = "<b>⏰ Sizning faol eslatmalaringiz:</b>" if reminders else "<b>⏰ Eslatmalar bo'limi:</b>\n\nHozircha faol eslatmalar yo'q."
    await message.answer(text, parse_mode="HTML", reply_markup=get_reminders_keyboard(reminders))

@reminders_router.callback_query(F.data == "add_new_reminder")
async def start_add_reminder(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddReminderState.enter_text)
    await callback.message.answer("Eslatma matnini kiriting (masalan: <i>Server to'lovini qilish</i>):", parse_mode="HTML")
    await callback.answer()

@reminders_router.message(AddReminderState.enter_text)
async def process_reminder_text(message: Message, state: FSMContext):
    await state.update_data(reminder_text=message.text.strip())
    await state.set_state(AddReminderState.enter_time)
    await message.answer(
        "Eslatma vaqtini quyidagi formatda kiriting:\n\n"
        "• Faqat vaqt (bugun uchun): <code>18:30</code>\n"
        "• Sana va vaqt: <code>2026-08-15 14:00</code>",
        parse_mode="HTML"
    )

@reminders_router.message(AddReminderState.enter_time)
async def process_reminder_time(message: Message, state: FSMContext, db_session: AsyncSession, bot: Bot):
    time_input = message.text.strip()
    now = datetime.now(local_tz)

    try:
        if len(time_input) == 5 and ":" in time_input:  # HH:MM
            parsed_time = datetime.strptime(time_input, "%H:%M").time()
            remind_dt = datetime.combine(now.date(), parsed_time)
            remind_dt = local_tz.localize(remind_dt)
            if remind_dt < now:
                await message.answer("⚠️ Kiritilgan vaqt o'tib ketgan! Kelajakdagi vaqtni kiriting:")
                return
        else:  # YYYY-MM-DD HH:MM
            naive_dt = datetime.strptime(time_input, "%Y-%m-%d %H:%M")
            remind_dt = local_tz.localize(naive_dt)
            if remind_dt < now:
                await message.answer("⚠️ Kiritilgan sana/vaqt o'tib ketgan!")
                return
    except ValueError:
        await message.answer("⚠️ Vaqt formati noto'g'ri! Qaytadan kiriting (Masalan: <code>18:30</code> yoki <code>2026-08-15 14:00</code>):", parse_mode="HTML")
        return

    data = await state.get_data()
    reminder_text = data["reminder_text"]

    # Bazaga saqlash
    new_reminder = Reminder(
        user_id=message.from_user.id,
        text=reminder_text,
        remind_at=remind_dt.replace(tzinfo=None)
    )
    db_session.add(new_reminder)
    await db_session.commit()

    # Scheduler ga biriktirish
    schedule_reminder(bot, new_reminder.id, message.from_user.id, reminder_text, remind_dt)

    await state.clear()
    await message.answer(
        f"✅ <b>Eslatma o'rnatildi!</b>\n\n"
        f"📌 <b>Matn:</b> {reminder_text}\n"
        f"⏰ <b>Vaqt:</b> {remind_dt.strftime('%Y-%m-%d %H:%M')}",
        parse_mode="HTML"
    )

@reminders_router.callback_query(F.data.startswith("del_rem_"))
async def delete_reminder(callback: CallbackQuery, db_session: AsyncSession):
    rem_id = int(callback.data.split("_")[2])
    reminder = await db_session.get(Reminder, rem_id)
    if reminder and reminder.user_id == callback.from_user.id:
        await db_session.delete(reminder)
        await db_session.commit()

    stmt = select(Reminder).where(Reminder.user_id == callback.from_user.id).order_by(Reminder.remind_at.asc())
    res = await db_session.execute(stmt)
    reminders = res.scalars().all()

    await callback.message.edit_reply_markup(reply_markup=get_reminders_keyboard(reminders))
    await callback.answer("Eslatma o'chirildi!")

@reminders_router.callback_query(F.data.startswith("info_rem_"))
async def show_reminder_info(callback: CallbackQuery, db_session: AsyncSession):
    rem_id = int(callback.data.split("_")[2])
    reminder = await db_session.get(Reminder, rem_id)
    if reminder and reminder.user_id == callback.from_user.id:
        time_str = reminder.remind_at.strftime("%Y-%m-%d %H:%M")
        info_text = f"⏰ Eslatma vaqti: {time_str}\n\n📌 Matn: {reminder.text}"
        await callback.answer(info_text, show_alert=True)
    else:
        await callback.answer("Eslatma topilmadi!", show_alert=True)