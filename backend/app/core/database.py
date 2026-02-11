from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text, inspect
from .config import settings


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # 数据库迁移：为已有表添加缺失的列
        def _get_columns(connection, table_name):
            insp = inspect(connection)
            if table_name not in insp.get_table_names():
                return None
            return [col['name'] for col in insp.get_columns(table_name)]

        columns = await conn.run_sync(lambda c: _get_columns(c, 'speech_configs'))
        if columns is not None and 'whisper_model' not in columns:
            await conn.execute(text(
                "ALTER TABLE speech_configs ADD COLUMN whisper_model VARCHAR(100) DEFAULT 'whisper-1'"
            ))
