import asyncio
import logging
from aiogram import Bot, Dispatcher
from config.config import config
from database.base import init_db, async_session_maker
from middlewares.db_middleware import DatabaseMiddleware
from handlers.start import start_router
from handlers.categories import category_router
from handlers.finance import finance_router
from handlers.reports import reports_router
from handlers.tasks import tasks_router
from handlers.reminders import reminders_router
from services.scheduler import scheduler, schedule_reminder
from sqlalchemy.future import select
from database.models import Reminder
from datetime import datetime

logging.basicConfig(level=logging.INFO)

async def restore_reminders(bot: Bot):
    """Bot qayta ishga tushganda o'tib ketmagan eslatmalarni scheduler ga yuklash"""
    async with async_session_maker() as session:
        stmt = select(Reminder).where(Reminder.remind_at > datetime.utcnow())
        res = await session.execute(stmt)
        reminders = res.scalars().all()
        for r in reminders:
            schedule_reminder(bot, r.id, r.user_id, r.text, r.remind_at)

async def main():
    await init_db()

    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher()

    dp.update.middleware(DatabaseMiddleware())

    # Routerlarni ulash
    dp.include_router(start_router)
    dp.include_router(category_router)
    dp.include_router(finance_router)
    dp.include_router(reports_router)
    dp.include_router(tasks_router)
    dp.include_router(reminders_router)

    # Scheduler ni ishga tushirish
    scheduler.start()
    await restore_reminders(bot)

    logging.info("Bot va Scheduler muvaffaqiyatli ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot to'xtatildi!")