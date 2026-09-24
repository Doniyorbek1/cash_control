from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.models import Category, Task

def get_categories_keyboard(categories: list[Category], prefix: str = "cat") -> InlineKeyboardMarkup:
    buttons = []
    row = []
    for cat in categories:
        row.append(InlineKeyboardButton(text=cat.name, callback_data=f"{prefix}_{cat.id}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    
    buttons.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_skip_description_keyboard(skip_callback: str = "skip_description") -> InlineKeyboardMarkup:
    kb = [
        [InlineKeyboardButton(text="⏩ Izohsiz davom etish", callback_data=skip_callback)],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_confirmation_keyboard(confirm_callback: str = "confirm_expense") -> InlineKeyboardMarkup:
    kb = [
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=confirm_callback),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_settings_keyboard() -> InlineKeyboardMarkup:
    kb = [
        [InlineKeyboardButton(text="➕ Yangi kategoriya qo'shish", callback_data="add_custom_category")],
        [InlineKeyboardButton(text="📋 Barcha kategoriyalarim", callback_data="list_categories")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_tasks_keyboard(tasks: list[Task]) -> InlineKeyboardMarkup:
    buttons = []
    for task in tasks:
        status_icon = "✅" if task.is_completed else "⬜"
        task_text = f"{status_icon} {task.title}"
        
        row = [
            InlineKeyboardButton(text=task_text, callback_data=f"toggle_task_{task.id}"),
            InlineKeyboardButton(text="🗑", callback_data=f"delete_task_{task.id}")
        ]
        buttons.append(row)
    
    buttons.append([InlineKeyboardButton(text="➕ Yangi vazifa qo'shish", callback_data="add_new_task")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)