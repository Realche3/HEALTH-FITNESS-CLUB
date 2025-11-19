"""
Trainer Model
-------------
Represents a gym trainer. Trainers can teach classes and conduct personal
training sessions.
"""

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from .base import Base


class Trainer(Base):
    """
    ORM class for the 'trainers' table.

    Attributes:
        id            (int): Primary key.
        name          (str): Trainer's full name.
        specialization(str): Area of expertise (e.g., strength, cardio).

    Relationships:
        sessions: List of PTSession entries.
        classes: List of Class entries.
        availabilities: List of TrainerAvailability time windows.
    """

    __tablename__ = "trainers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    specialization = Column(String)

    sessions = relationship(
        "PTSession",
        back_populates="trainer",
        cascade="all, delete-orphan",
    )
    classes = relationship(
        "Class",
        back_populates="trainer",
        cascade="all, delete-orphan",
    )
    availabilities = relationship(
        "TrainerAvailability",
        back_populates="trainer",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Trainer id={self.id} name={self.name!r}>"
