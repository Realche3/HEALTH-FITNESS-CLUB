"""
Room Model
----------
Represents a physical room inside the fitness club. Rooms host group classes
and can also be booked for PT sessions and contain equipment.
"""

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from .base import Base


class Room(Base):
    """
    ORM class for the 'rooms' table.

    Attributes:
        id       (int): Primary key.
        name     (str): Name of the room (e.g., "Yoga Studio").
        capacity (int): Maximum number of people the room can hold.

    Relationships:
        classes: List of Class entries hosted in this room.
        sessions: List of PTSession entries conducted in this room.
        equipment: List of Equipment items located in this room.
    """

    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    capacity = Column(Integer, nullable=False)

    classes = relationship(
        "Class",
        back_populates="room",
        cascade="all, delete-orphan",
    )
    sessions = relationship(
        "PTSession",
        back_populates="room",
        cascade="all, delete-orphan",
    )
    equipment = relationship(
        "Equipment",
        back_populates="room",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Room id={self.id} name={self.name!r}>"
