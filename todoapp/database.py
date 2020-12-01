from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from starlette.requests import Request

DbModel = declarative_base()


def get_db(request: Request) -> AsyncSession:
    return request.state.db
