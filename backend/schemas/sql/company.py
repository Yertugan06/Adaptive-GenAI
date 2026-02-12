from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship
from .base import Base

class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    industry = Column(String(100), nullable = False)
    plan_tier = Column(String(50), default="trial")
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    users = relationship("User", back_populates="company")