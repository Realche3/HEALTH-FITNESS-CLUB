"""
Class Model
-----------
Represents a scheduled group fitness class taught by a trainer in a room.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


class Class(Base):
    """
    ORM class for the 'classes' table.

    Attributes:
        id            (int): Primary key.
        name          (str): Class name (e.g., Yoga, Spin).
        capacity      (int): Max participants.
        trainer_id    (int): FK to trainers.id.
        room_id       (int): FK to rooms.id.
        schedule_time (datetime): Date and time of the class.

    Relationships:
        trainer: Trainer teaching the class.
        room: Room where the class is held.
        registrations: List of ClassRegistration entries (members registered).
    """

    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    capacity = Column(Integer, nullable=False)
    trainer_id = Column(Integer, ForeignKey("trainers.id"), nullable=False)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    schedule_time = Column(DateTime, nullable=False)

    trainer = relationship("Trainer", back_populates="classes")
    room = relationship("Room", back_populates="classes")

    registrations = relationship(
        "ClassRegistration",
        back_populates="gym_class",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Class id={self.id} name={self.name!r} trainer_id={self.trainer_id}>"
