from contextvars import ContextVar

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session as _scoped_session
from sqlalchemy.util import ScopedRegistry

DbModel = declarative_base()


def get_db(request) -> AsyncSession:
    yield request.state.db


class ContextVarRegistry(ScopedRegistry):
    def __init__(self, create_func):
        self.create_func = create_func
        self.registry = ContextVar('value')
        self._token = None

    def __call__(self):
        try:
            return self.registry.get()
        except LookupError:
            val = self.create_func()
            self._token = self.registry.set(val)
            return val

    def has(self):
        return bool(self._token)

    def set(self, obj):
        self._token = self.registry.set(obj)
    
    def clear(self):
        if self._token:
            self.registry.reset(self._token)


class scoped_session(_scoped_session):
    def __init__(self, session_factory, scopefunc=None):
        self.session_factory = session_factory

        if scopefunc:
            self.registry = ScopedRegistry(session_factory, scopefunc)
        else:
            self.registry = ContextVarRegistry(session_factory)