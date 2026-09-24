from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from config.config import config

engine = create_async_engine(
    config.DATABASE_URL,
    echo=False
)

async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

class Base(DeclarativeBase):
    pass

async def init_db():
    """Barcha jadvallarni yaratish va mavjud bazani yangilash (migration)"""
    async with engine.begin() as conn:
        from database.models import Base as ModelsBase
        await conn.run_sync(ModelsBase.metadata.create_all)
        
        # Agar categories jadvalida 'type' ustuni bo'lmasa, uni xatosiz qo'shish
        try:
            await conn.execute(text("ALTER TABLE categories ADD COLUMN type VARCHAR DEFAULT 'expense'"))
        except Exception:
            pass  # Agar ustun allaqachon mavjud bo'lsa, xatolik inobatga olinmaydi