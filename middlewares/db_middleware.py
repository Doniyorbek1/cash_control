from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TgUser
from sqlalchemy.future import select
from database.base import async_session_maker
from database.models import User, Category, TransactionType

DEFAULT_EXPENSE_CATEGORIES = [
    "🍔 Oziq-ovqat",
    "🚕 Transport",
    "🏠 Kommunal",
    "🎬 O'yin-kulgi",
    "🛍 Xaridlar",
    "💊 Salomatlik"
]

DEFAULT_INCOME_CATEGORIES = [
    "💼 Oylik maosh",
    "💻 Frilans / Qo'shimcha",
    "📈 Investitsiya",
    "🎁 Sovg'a",
    "🔄 Boshqa kirim"
]

class DatabaseMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        async with async_session_maker() as session:
            user: TgUser = data.get("event_from_user")
            
            if user:
                stmt = select(User).where(User.telegram_id == user.id)
                result = await session.execute(stmt)
                db_user = result.scalar_one_or_none()

                if not db_user:
                    db_user = User(
                        telegram_id=user.id,
                        username=user.username,
                        first_name=user.first_name
                    )
                    session.add(db_user)
                    await session.flush()

                    # Standart xarajat kategoriyalari
                    for cat_name in DEFAULT_EXPENSE_CATEGORIES:
                        category = Category(
                            user_id=user.id,
                            name=cat_name,
                            type=TransactionType.EXPENSE,
                            is_default=True
                        )
                        session.add(category)

                    # Standart daromad kategoriyalari
                    for cat_name in DEFAULT_INCOME_CATEGORIES:
                        category = Category(
                            user_id=user.id,
                            name=cat_name,
                            type=TransactionType.INCOME,
                            is_default=True
                        )
                        session.add(category)

                    await session.commit()

            data["db_session"] = session
            return await handler(event, data)