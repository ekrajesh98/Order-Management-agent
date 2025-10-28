import contextlib
import logging
from collections.abc import AsyncIterator
from typing import Any, Iterator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker

from src.config import settings


class DatabaseSessionManager:
    def __init__(self, url: str, engine_kwargs: dict[str, Any]) -> None:
        logging.debug("Initializing DatabaseSessionManager")
        self._engine: AsyncEngine | None = create_async_engine(url, **engine_kwargs)
        self._sessionmaker: async_sessionmaker[AsyncSession] | None = (
            async_sessionmaker(
                autocommit=False,
                bind=self._engine,
                expire_on_commit=False,
            )
        )

    @contextlib.asynccontextmanager
    async def connect(self) -> AsyncIterator[AsyncConnection]:
        logging.debug("Creating database connection")
        if self._engine is None:
            msg = "Database ENGINE is not initialized"
            raise RuntimeError(msg)

        async with self._engine.begin() as conn:
            try:
                yield conn
            except Exception:
                await conn.rollback()
                raise
        logging.debug("Closing database connection")

    @contextlib.asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        logging.debug("Creating database session")
        if self._sessionmaker is None:
            msg = "Database SESSIONMAKER is not initialized"
            raise RuntimeError(msg)

        session = self._sessionmaker()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            logging.debug("Closing database session")
            await session.close()

    async def close(self) -> None:
        logging.debug("Closing DatabaseSessionManager")
        if self._engine is not None:
            await self._engine.dispose()

        self._engine = None
        self._sessionmaker = None


database_session_manager = DatabaseSessionManager(
    url=settings.DB.URL,
    engine_kwargs={},
)


async def get_db_connection() -> AsyncIterator[AsyncConnection]:
    async with database_session_manager.connect() as conn:
        yield conn


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async with database_session_manager.session() as session:
        yield session


class SyncDatabaseSessionManager:
    def __init__(self, url: str, engine_kwargs: dict[str, Any]) -> None:
        logging.debug("Initializing SyncDatabaseSessionManager")
        self._engine = create_engine(url, **engine_kwargs)
        self._sessionmaker = sessionmaker(
            bind=self._engine,
            autocommit=False,
            expire_on_commit=False,
        )

    @contextlib.contextmanager
    def session(self) -> Iterator[Session]:
        session = self._sessionmaker()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


sync_database_session_manager = SyncDatabaseSessionManager(
    url=settings.DB.URL_SYNC,
    engine_kwargs={},
)


@contextlib.contextmanager
def get_sync_db_session() -> Iterator[Session]:
    with sync_database_session_manager.session() as session:
        yield session
