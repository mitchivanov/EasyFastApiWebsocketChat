from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.models import Base, Message
from typing import AsyncGenerator, List, Dict
from sqlalchemy import select

DATABASE_URL = 'sqlite+aiosqlite:///chat_history.db'

engine = create_async_engine(DATABASE_URL, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def save_message(room_id: int, user_id: int, username: str, message: str, timestamp: str):
    async with AsyncSessionLocal() as session:
        new_message = Message(
            room_id=room_id,
            user_id=user_id,
            username=username,
            message=message,
            timestamp=timestamp
        )
        session.add(new_message)
        await session.commit()


async def get_room_history(room_id: int) -> List[Dict]:
    async with AsyncSessionLocal() as session:
        stmt = select(Message).where(Message.room_id == room_id).order_by(Message.id.asc())
        result = await session.execute(stmt)
        messages = result.scalars().all()
        
        return [
            {
                "user_id": msg.user_id,
                "username": msg.username,
                "message": msg.message,
                "timestamp": msg.timestamp
            }
            for msg in messages
        ]
