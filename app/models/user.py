from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text
from sqlalchemy.sql import func
from ..database import Base
import uuid

class User(Base):
    __tablename__ = "r_users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False)
    user_id = Column(String(50), unique=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    is_active = Column(Boolean, default=True)
    trial_access_granted = Column(Boolean, default=False)
    trial_access_date = Column(DateTime)
    access_count = Column(Integer, default=0) 