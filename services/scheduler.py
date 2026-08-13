from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
import pytz
from config.config import config

# Toshkent vaqt mintaqasi bilan ishlaymiz
tz = pytz.timezone(config.DEFAULT_TIMEZONE)
scheduler = AsyncIOScheduler(timezone=tz)

async def send_reminder_notification(bot: Bot, user_id: int, text: str):
    """Vaqti kelgan eslatmani Telegram orqali yuborish"""
    try:
        await bot.send_message(
            chat_id=user_id,
            text=f"⏰ <b>ESLATMA!</b>\n\n📌 {text}",
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Eslatma yuborishda xatolik ({user_id}): {e}")

def schedule_reminder(bot: Bot, reminder_id: int, user_id: int, text: str, remind_at: datetime):
    """Yangi eslatmani scheduler ga topshiriq (job) qilib qo'shish"""
    job_id = f"reminder_{reminder_id}"
    scheduler.add_job(
        send_reminder_notification,
        'date',
        run_date=remind_at,
        args=[bot, user_id, text],
        id=job_id,
        replace_existing=True
    )