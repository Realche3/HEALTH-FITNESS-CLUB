# models/equipment.py
"""
Equipment Model
----------------
Represents a piece of equipment in the fitness club, such as a treadmill or
weight machine. Each piece of equipment is associated with a room and can
have maintenance issues logged against it.
"""

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base


class Equipment(Base):
    """
    ORM class for the 'equipment' table.

    Attributes:
        id       (int): Primary key.
        name     (str): Name of the equipment (e.g., "Treadmill #1").
        type     (str): Optional type/category (e.g., "cardio", "strength").
        status   (str): Operational status (e.g., "operational", "out_of_order").
        room_id  (int): FK to rooms.id indicating where the equipment is located.

    Relationships:
        room: The Room where the equipment resides.
        issues: List of EquipmentIssue records associated with this equipment.
    """

    __tablename__ = "equipment"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=True)
    status = Column(String, nullable=False, default="operational")
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)

    room = relationship("Room", back_populates="equipment")
    issues = relationship(
        "EquipmentIssue",
        back_populates="equipment",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<Equipment id={self.id} name={self.name!r} "
            f"status={self.status!r} room_id={self.room_id}>"
        )
