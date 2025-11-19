# models/pt_session.py
"""
PTSession Model
---------------
Represents a one-on-one personal training session between a member and a trainer,
optionally booked in a specific room at a specific time.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


class PTSession(Base):
    """
    ORM class for the 'pt_sessions' table.

    Attributes:
        id (int): Primary key.
        member_id (int): Foreign key to members.id.
        trainer_id (int): Foreign key to trainers.id.
        room_id (int | None): Foreign key to rooms.id (optional).
        start_time (datetime): When the session starts.
        end_time (datetime | None): When the session ends (can be null if not finished).
        status (str): Status of the session (e.g., 'scheduled', 'completed', 'cancelled').

    Relationships:
        member: Many-to-one relationship with Member.
        trainer: Many-to-one relationship with Trainer.
        room: Many-to-one relationship with Room.
    """
    __tablename__ = "pt_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    trainer_id = Column(Integer, ForeignKey("trainers.id"), nullable=False)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    status = Column(String, nullable=False, default="scheduled")

    # Relationships
    member = relationship("Member", back_populates="sessions")
    trainer = relationship("Trainer", back_populates="sessions")
    room = relationship("Room", back_populates="sessions")

    def __repr__(self) -> str:
        return (
            f"<PTSession id={self.id} member_id={self.member_id} "
            f"trainer_id={self.trainer_id} status={self.status!r}>"
        )
