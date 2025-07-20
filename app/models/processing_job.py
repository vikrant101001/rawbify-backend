from sqlalchemy import Column, String, DateTime, Integer, Text, BigInteger
from sqlalchemy.sql import func
from ..database import Base
import uuid
import json

class ProcessingJob(Base):
    __tablename__ = "r_processing_jobs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(50), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    prompt = Column(Text, nullable=False)
    status = Column(String(20), default='pending')
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime)
    processing_summary = Column(Text)  # Store as JSON string for SQLite
    output_file_path = Column(String(500))
    error_message = Column(Text) 