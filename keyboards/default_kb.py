from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_keyboard() -> ReplyKeyboardMarkup:
    kb = [
        [
            KeyboardButton(text="💸 Xarajat qo'shish"),
            KeyboardButton(text="📊 Hisobotlar")
        ],
        [
            KeyboardButton(text="📝 To-Do List"),
            KeyboardButton(text="⏰ Eslatmalar")
        ],
        [
            KeyboardButton(text="⚙️ Sozlamalar (Kategoriyalar)")
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        persistent=True
    )