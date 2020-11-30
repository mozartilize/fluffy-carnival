import asyncio
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..users.models import User

user_router = APIRouter()


@user_router.get("")
async def get_users(DbSession: AsyncSession = Depends(get_db)):
    with DbSession() as db_session:
        result = await db_session.execute(
            select(User.id, User.email, User.first_name, User.last_name, User.created_at)
        )
    return result.all()
