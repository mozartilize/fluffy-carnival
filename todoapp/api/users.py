from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine

from ..database import get_db
from ..users.models import User

user_router = APIRouter()


@user_router.get("")
async def get_users(db: AsyncEngine = Depends(get_db)):
    async with db.connect() as conn:
        result = await conn.execute(
            select(User.id, User.email, User.first_name, User.last_name, User.created_at)
        )
    return result.all()
