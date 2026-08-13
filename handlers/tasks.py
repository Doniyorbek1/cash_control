from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database.models import Task
from utils.states import AddTaskState
from keyboards.inline_kb import get_tasks_keyboard

tasks_router = Router()

@tasks_router.message(F.text == "📝 To-Do List")
async def cmd_todo_list(message: Message, db_session: AsyncSession):
    stmt = select(Task).where(Task.user_id == message.from_user.id).order_by(Task.created_at.desc())
    res = await db_session.execute(stmt)
    tasks = res.scalars().all()

    if not tasks:
        text = "<b>📝 To-Do List:</b>\n\nSizda hozircha hech qanday vazifa yo'q."
    else:
        text = "<b>📝 Sizning vazifalaringiz:</b>\n\nBajarilganligini belgilash uchun ustiga bosing:"

    await message.answer(text, parse_mode="HTML", reply_markup=get_tasks_keyboard(tasks))

@tasks_router.callback_query(F.data == "add_new_task")
async def start_add_task(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddTaskState.enter_title)
    await callback.message.answer("Yangi vazifa nomini kiriting (masalan: <i>Serverlarni bekash qilish</i>):", parse_mode="HTML")
    await callback.answer()

@tasks_router.message(AddTaskState.enter_title)
async def process_task_title(message: Message, state: FSMContext, db_session: AsyncSession):
    title = message.text.strip()

    new_task = Task(
        user_id=message.from_user.id,
        title=title,
        is_completed=False
    )
    db_session.add(new_task)
    await db_session.commit()

    await state.clear()
    
    # Yangilangan ro'yxatni ko'rsatish
    stmt = select(Task).where(Task.user_id == message.from_user.id).order_by(Task.created_at.desc())
    res = await db_session.execute(stmt)
    tasks = res.scalars().all()

    await message.answer(
        f"✅ <b>Yangi vazifa qo'shildi:</b> {title}",
        parse_mode="HTML",
        reply_markup=get_tasks_keyboard(tasks)
    )

@tasks_router.callback_query(F.data.startswith("toggle_task_"))
async def toggle_task_status(callback: CallbackQuery, db_session: AsyncSession):
    task_id = int(callback.data.split("_")[2])
    
    task = await db_session.get(Task, task_id)
    if task and task.user_id == callback.from_user.id:
        task.is_completed = not task.is_completed  # Statusni teskarisiga o'zgartirish
        await db_session.commit()

    # Ro'yxatni qayta yuklab klaviaturani yangilash
    stmt = select(Task).where(Task.user_id == callback.from_user.id).order_by(Task.created_at.desc())
    res = await db_session.execute(stmt)
    tasks = res.scalars().all()

    await callback.message.edit_reply_markup(reply_markup=get_tasks_keyboard(tasks))
    await callback.answer()

@tasks_router.callback_query(F.data.startswith("delete_task_"))
async def delete_task(callback: CallbackQuery, db_session: AsyncSession):
    task_id = int(callback.data.split("_")[2])

    task = await db_session.get(Task, task_id)
    if task and task.user_id == callback.from_user.id:
        await db_session.delete(task)
        await db_session.commit()

    # Ro'yxatni qayta yuklab klaviaturani yangilash
    stmt = select(Task).where(Task.user_id == callback.from_user.id).order_by(Task.created_at.desc())
    res = await db_session.execute(stmt)
    tasks = res.scalars().all()

    await callback.message.edit_reply_markup(reply_markup=get_tasks_keyboard(tasks))
    await callback.answer("Vazifa o'chirildi!")