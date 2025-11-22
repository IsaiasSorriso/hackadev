from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from .db import Base

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    role = Column(String(10))  # "user" ou "assistant" ou "system"
    content = Column(Text)
    session_id = Column(String(100), index=True, default="default")
    created_at = Column(DateTime, default=datetime.utcnow)
