import logging

from fastapi import FastAPI, HTTPException, Response
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import AsyncAdaptedQueuePool
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from .api.users import user_router
from .config import get_settings
from .database import scoped_session

logger = logging.getLogger(__name__)


def create_app():
    api = FastAPI()

    settings = get_settings()
    db_engine = create_async_engine(
        settings.sqlalchemy_database_uri,
        poolclass=AsyncAdaptedQueuePool,
        pool_recycle=180,
    )
    Session = scoped_session(sessionmaker(bind=db_engine, class_=AsyncSession, expire_on_commit=False))

    api.include_router(user_router, prefix='/users')

    @api.middleware("http")
    async def db_session_middleware(request: Request, call_next):
        request.state.db = Session()
        resp = Response('Internal Server Error', 500)
        try:
            resp = await call_next(request)
        except Exception as e:
            logger.exception(e)
            await Session.remove()
        return resp

    return api


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
        result = db.session.execute(
            select(User.id, User.email, User.first_name, User.last_name, User.created_at)
        )
        result.all()
        return jsonify({'ok': True})

    return app
