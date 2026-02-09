from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from .base import Base
from pydantic import BaseModel, EmailStr
# Schemas 


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    company_id: int
    role: str = "employee"
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id"))
    name = Column(String(100))
    role = Column(String(50))
    hashed_password = Column(String(255))
    email = Column(String(255), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    company = relationship("Company", back_populates="users")
    events = relationship("GenerationEvent", back_populates="user")