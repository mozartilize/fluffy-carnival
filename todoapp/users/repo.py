from typing import List, Union, NoReturn
from uuid import uuid1

from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession
from faker import Faker

from .models import User


async def insert_users(db: AsyncSession, users: List[User]) -> NoReturn:
    db.sync_session.bulk_save_objects(users)
    await db.commit()


async def autogen_users_and_insert_to_db(db: AsyncSession, total: int, batch: int) -> NoReturn:
    faker = Faker()
    for i in range(int(total / batch)):
        users = [
            User(
                email=faker.email(),
                first_name=faker.first_name(),
                last_name=faker.last_name(),
                firebase_auth_uuid=uuid1().hex,
            )
            for j in range(batch)
        ]
        await insert_users(db, users)
