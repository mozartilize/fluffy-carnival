from fastapi import FastAPI, HTTPException
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from .api.users import user_router
from .config import get_settings
from .database import scoped_session


def create_app():
    api = FastAPI()

    settings = get_settings()
    db_engine = create_async_engine(
        settings.sqlalchemy_database_url, 
        poolclass=NullPool
    )
    Session = scoped_session(sessionmaker(db_engine, class_=AsyncSession))

    api.include_router(user_router, prefix='/users')


    @api.middleware("http")
    async def db_session_middleware(request: Request, call_next):
        request.state.db = Session
        resp = await call_next(request)
        Session.remove()
        return resp

    return api