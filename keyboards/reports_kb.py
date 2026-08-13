from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_reports_keyboard() -> InlineKeyboardMarkup:
    kb = [
        [
            InlineKeyboardButton(text="📅 Bugun", callback_data="report_today"),
            InlineKeyboardButton(text="📆 Shu hafta", callback_data="report_week")
        ],
        [
            InlineKeyboardButton(text="📊 Shu oy", callback_data="report_month")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)