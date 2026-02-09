from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, func, CheckConstraint
from sqlalchemy.orm import relationship
from .base import Base

class GenerationEvent(Base):
    __tablename__ = "generation_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    mongo_event_id = Column(String(50)) # Soft link to MongoDB
    rating = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (CheckConstraint('rating >= 1 AND rating <= 5'),)

    # Relationships
    user = relationship("User", back_populates="events")