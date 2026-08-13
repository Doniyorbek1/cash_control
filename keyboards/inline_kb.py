from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.models import Category
from database.models import Task


def get_categories_keyboard(categories: list[Category]) -> InlineKeyboardMarkup:
    buttons = []
    row = []
    for cat in categories:
        row.append(InlineKeyboardButton(text=cat.name, callback_data=f"cat_{cat.id}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
        
    buttons.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_settings_keyboard() -> InlineKeyboardMarkup:
    kb = [
        [InlineKeyboardButton(text="➕ Yangi kategoriya qo'shish", callback_data="add_custom_category")],
        [InlineKeyboardButton(text="📋 Barcha kategoriyalarim", callback_data="list_categories")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Tasdiqlash va Bekor qilish tugmalari"""
    kb = [
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="confirm_expense"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_tasks_keyboard(tasks: list[Task]) -> InlineKeyboardMarkup:
    buttons = []
    for task in tasks:
        # Bajarilgan bo'lsa ✅, bajarilmagan bo'lsa ❌ boks qo'yiladi
        status_icon = "✅" if task.is_completed else "🔲"
        task_text = f"{status_icon} {task.title}"
        
        # Vazifa holatini o'zgartirish va o'chirish tugmalari
        row = [
            InlineKeyboardButton(text=task_text, callback_data=f"toggle_task_{task.id}"),
            InlineKeyboardButton(text="🗑", callback_data=f"delete_task_{task.id}")
        ]
        buttons.append(row)
        
    buttons.append([InlineKeyboardButton(text="➕ Yangi vazifa qo'shish", callback_data="add_new_task")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)