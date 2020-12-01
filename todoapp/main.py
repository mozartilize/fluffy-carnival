import logging

from fastapi import FastAPI, HTTPException, Response, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import AsyncAdaptedQueuePool, NullPool
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from .api.users import user_router
from .config import get_settings
from .database import get_db

logger = logging.getLogger(__name__)


def create_fastapi_app():
    api = FastAPI()

    settings = get_settings()
    db_engine = create_async_engine(
        settings.sqlalchemy_database_uri,
        poolclass=AsyncAdaptedQueuePool,
        pool_recycle=180,
    )
    DbSession = sessionmaker(bind=db_engine, class_=AsyncSession, expire_on_commit=False)

    @api.get('/ping')
    async def ping_db(db_session: AsyncSession = Depends(get_db)):
        result = await db_session.execute(text('select 1'))

        return result.scalar_one()

    api.include_router(user_router, prefix='/users')

    if settings.preload:
        @api.on_event('startup')
        async def dispose_db_engine_for_gunicorn_preload():
            await db_engine.dispose()


    @api.middleware("http")
    async def db_session_middleware(request: Request, call_next):
        request.state.db = DbSession()
        resp = Response('Internal Server Error', 500)
        try:
            resp = await call_next(request)
        finally:
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
    app.config['SQLALCHEMY_DATABASE_URI'] = settings.sqlalchemy_database_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db = SQLAlchemy(app)

    @app.route('/users', methods=['GET'])
    def users():
        result = db.engine.execute(
            select(User.id, User.email, User.first_name, User.last_name, User.created_at)
        )
        result.all()
        return jsonify({'ok': True})

    return app
