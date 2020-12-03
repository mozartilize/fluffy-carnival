import asyncio
from datetime import datetime, timedelta
import logging
from typing import Union

from fastapi import FastAPI, HTTPException, Response, Depends
from sqlalchemy import text, event
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import AsyncAdaptedQueuePool, NullPool
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, AsyncConnection
from starlette.requests import Request

from .api.users import user_router
from .config import get_settings
from .database import get_db, LazyAsyncConnection

logger = logging.getLogger(__name__)


def create_fastapi_app():
    api = FastAPI()

    settings = get_settings()
    db_engine: AsyncEngine = create_async_engine(
        settings.sqlalchemy_database_uri,
        poolclass=AsyncAdaptedQueuePool,
        pool_recycle=180,
    )
    autocommit_db_engine: AsyncEngine = create_async_engine(
        settings.sqlalchemy_database_uri,
        pool=db_engine.pool,
        connect_args={"autocommit": True},
    )
    DbSession: AsyncSession = sessionmaker(
        bind=db_engine, class_=AsyncSession, expire_on_commit=False
    )
    read_db_conn = LazyAsyncConnection(autocommit_db_engine)

    @event.listens_for(autocommit_db_engine.sync_engine, "after_execute")
    def receive_after_execute(conn, *args):
        conn.connection.info["last_exec_at"] = datetime.now()

    @api.get("/ping")
    async def ping_db(db_session: AsyncSession = Depends(get_db)):
        result = await db_session.execute(text("select 1"))

        return result.scalar_one()

    api.include_router(user_router, prefix="/users")

    if settings.preload:

        @api.on_event("startup")
        async def dispose_db_engine_for_gunicorn_preload():
            await db_engine.dispose()

    @api.middleware("http")
    async def db_session_middleware(request: Request, call_next):
        request.state.db: Union[AsyncConnection, AsyncSession]
        if request.method not in ["POST", "PUT", "PATCH", "DELETE"]:
            if (
                read_db_conn.last_exec_at
                and datetime.now() - read_db_conn.last_exec_at >= timedelta(seconds=180)
            ):
                await read_db_conn.dispose()
            request.state.db = read_db_conn
        else:
            request.state.db = DbSession()
        resp = await call_next(request)
        if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            await request.state.db.close()
        return resp

    return api


fastapiapp = create_fastapi_app()


def create_flask_app():
    from flask import Flask, jsonify
    from flask_sqlalchemy import SQLAlchemy
    from sqlalchemy import select

    from .users.models import User

    app = Flask(__name__)

    settings = get_settings()
    app.config["SQLALCHEMY_DATABASE_URI"] = settings.sqlalchemy_database_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db = SQLAlchemy(app)

    @app.route("/users", methods=["GET"])
    def users():
        result = db.engine.execute(
            select(
                User.id, User.email, User.first_name, User.last_name, User.created_at
            )
        )
        result.all()
        return jsonify({"ok": True})

    return app
