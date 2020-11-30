from contextvars import ContextVar
import logging

from sqlalchemy import exc as sa_exc
from sqlalchemy.orm import class_mapper
from sqlalchemy.orm import exc as orm_exc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session as _scoped_session
from sqlalchemy.util import ScopedRegistry, create_proxy_methods
from starlette.requests import Request

DbModel = declarative_base()
logger = logging.getLogger(__name__)

def get_db(request: Request) -> AsyncSession:
    return request.state.db


class ContextVarRegistry(ScopedRegistry):
    def __init__(self, create_func):
        self.create_func = create_func
        self.registry = ContextVar('value')
        self._token = ContextVar('value')

    def __call__(self):
        try:
            return self.registry.get()
        except LookupError:
            val = self.create_func()
            self._token.set(self.registry.set(val))
            return val

    def has(self):
        try:
            self._token.get()
        except LookupError:
            return False
        return True

    def set(self, obj):
        self._token.set(self.registry.set(obj))
    
    def clear(self):
        try:
            self.registry.reset(self._token.get())
        except LookupError:
            pass


@create_proxy_methods(
    AsyncSession,
    ":class:`_asyncio.AsyncSession`",
    ":class:`scoped_session`",
    classmethods=["close_all", "object_session", "identity_key"],
    methods=[
        "__contains__",
        "__iter__",
        "add",
        "add_all",
        "begin",
        "begin_nested",
        "close",
        "commit",
        "connection",
        "delete",
        "execute",
        "expire",
        "expire_all",
        "expunge",
        "expunge_all",
        "flush",
        "get_bind",
        "is_modified",
        "merge",
        "refresh",
        "rollback",
    ],
    attributes=[
        "bind",
        "dirty",
        "deleted",
        "new",
        "identity_map",
        "is_active",
        "autoflush",
        "no_autoflush",
        "info",
        "autocommit",
    ],
)
class scoped_session:
    def __init__(self, session_factory, scopefunc=None):
        self.session_factory = session_factory
        if scopefunc:
            self.registry = ScopedRegistry(session_factory, scopefunc)
        else:
            self.registry = ContextVarRegistry(session_factory)
    
    @property
    def _proxied(self):
        return self.registry()

    def __call__(self, **kw):
        if kw:
            if self.registry.has():
                raise sa_exc.InvalidRequestError(
                    "Scoped session is already present; "
                    "no new arguments may be specified."
                )
            else:
                sess = self.session_factory(**kw)
                self.registry.set(sess)
                return sess
        else:
            return self.registry()

    async def remove(self):
        if self.registry.has():
            await self.registry().close()
        self.registry.clear()

    
    def configure(self, **kwargs):

        if self.registry.has():
            warn(
                "At least one scoped session is already present. "
                " configure() can not affect sessions that have "
                "already been created."
            )

        self.session_factory.configure(**kwargs)

    def query_property(self, query_cls=None):

        class query(object):
            def __get__(s, instance, owner):
                try:
                    mapper = class_mapper(owner)
                    if mapper:
                        if query_cls:
                            # custom query class
                            return query_cls(mapper, session=self.registry())
                        else:
                            # session's configured query class
                            return self.registry().query(mapper)
                except orm_exc.UnmappedClassError:
                    return None

        return query()
