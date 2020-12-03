from sqlalchemy.ext.asyncio import AsyncSession, AsyncConnection
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.util import await_only
from starlette.requests import Request

DbModel = declarative_base()


class LazyAsyncConnection:
    def __init__(self, engine):
        self._engine = engine
        self._conn = AsyncConnection(self._engine)

    def __getattribute__(self, attr):
        if attr in ['_engine', '_conn', 'last_exec_at', 'dispose']:
            return super().__getattribute__(attr)
        if not self._conn.sync_connection:
            self._conn.sync_connection = self._engine.sync_engine.connect()

        return getattr(self._conn, attr)

    @property
    def last_exec_at(self):
        if self._conn.sync_connection:
            return self._conn.sync_connection.connection.info.get('last_exec_at')

    async def dispose(self):
        await self._conn.invalidate()
        await self._conn.close()
        self._conn = AsyncConnection(self._engine)



def get_db(request: Request) -> AsyncSession:
    return request.state.db
