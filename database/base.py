from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from config.config import config

# SQLite bo'lsa multiprocess va foreign key qo'llab-quvvatlashini yoqamiz
engine = create_async_engine(
    config.DATABASE_URL,
    echo=False,  # SQL so'rovlar terminalda ko'rinishi uchun True qilsa bo'ladi
)

async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

class Base(DeclarativeBase):
    pass

async def init_db():
    """Barcha jadvallarni bazada avtomatik yaratish"""
    async with engine.begin() as conn:
        from database.models import Base as ModelsBase
        await conn.run_sync(ModelsBase.metadata.create_all)