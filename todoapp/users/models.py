from datetime import datetime

from sqlalchemy import Column, String, Boolean, DateTime, Integer

from ..database import DbModel


class User(DbModel):
    __tablename__ = "portal_auth_users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(length=255), index=True, nullable=False)
    first_name = Column(String(length=255))
    last_name = Column(String(length=255))
    firebase_auth_uuid = Column(String(length=255), index=True, nullable=False)
    is_unsubscribed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
