from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.declarative import declarative_base

DbModel = declarative_base()


def get_db(request) -> AsyncEngine:
    return request.state.db