import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher
from aiogram.types import Update
from a2wsgi import ASGIMiddleware

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

# Bot va Dispatcher yaratish
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()

# Middleware va Routerlarni ulash
dp.update.middleware(DatabaseMiddleware())
dp.include_router(start_router)
dp.include_router(category_router)
dp.include_router(finance_router)
dp.include_router(reports_router)
dp.include_router(tasks_router)
dp.include_router(reminders_router)

WEBHOOK_URL = f"{config.WEBHOOK_HOST}{config.WEBHOOK_PATH}"

async def restore_reminders():
    """Bot yoqilganda eslatmalarni qayta yuklash"""
    async with async_session_maker() as session:
        stmt = select(Reminder).where(Reminder.remind_at > datetime.utcnow())
        res = await session.execute(stmt)
        reminders = res.scalars().all()
        for r in reminders:
            schedule_reminder(bot, r.id, r.user_id, r.text, r.remind_at)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI ishga tushganda va to'xtaganda bajariladigan amallar"""
    await init_db()
    
    # Webhook o'rnatish
    await bot.set_webhook(url=WEBHOOK_URL, drop_pending_updates=True)
    logging.info(f"Webhook o'rnatildi: {WEBHOOK_URL}")

    # Scheduler va eslatmalarni tiklash
    scheduler.start()
    await restore_reminders()

    yield

    # O'chayotganda webhookni to'zalash va schedulerni to'xtatish
    scheduler.shutdown()
    await bot.delete_webhook()
    await bot.session.close()

app = FastAPI(lifespan=lifespan)

@app.post(config.WEBHOOK_PATH)
async def bot_webhook(request: Request):
    """Telegram'dan kelgan so'rovlarni aiogram dispatcher'iga uzatish"""
    update_data = await request.json()
    update = Update(**update_data)
    await dp.feed_update(bot, update)
    return {"status": "ok"}

# PythonAnywhere WSGI tushunishi uchun ASGIMiddleware yordamida o'rab olamiz
wsgi_app = ASGIMiddleware(app)