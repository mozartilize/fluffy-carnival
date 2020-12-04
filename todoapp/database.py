from sqlalchemy.ext.asyncio import AsyncSession, AsyncConnection
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.util import await_only
from starlette.requests import Request

DbModel = declarative_base()


class LazyAsyncConnection(AsyncConnection):
    @property
    def last_exec_at(self):
        if self.sync_connection:
            return self.sync_connection.connection.info.get("last_exec_at")

    def _sync_connection(self):
        if not self.sync_connection:
            self.sync_connection = self.sync_engine.connect()
        return self.sync_connection

    async def dispose(self):
        await self.invalidate()
        await self.close()
        self.sync_connection = None


def get_db(request: Request) -> AsyncSession:
    return request.state.db
