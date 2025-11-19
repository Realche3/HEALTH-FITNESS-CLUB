# models/trainer_availability.py
"""
TrainerAvailability Model
-------------------------
Represents a time window during which a trainer is available to teach
classes or conduct personal training sessions.

For simplicity, this implementation uses individual time intervals
(start_time, end_time) rather than recurring weekly slots, which still
satisfies the requirement to define and manage availability periods.
"""

from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base


class TrainerAvailability(Base):
    """
    ORM class for the 'trainer_availabilities' table.

    Attributes:
        id         (int): Primary key.
        trainer_id (int): FK to trainers.id.
        start_time (datetime): Start of availability window.
        end_time   (datetime): End of availability window.

    Relationships:
        trainer: The Trainer this availability belongs to.
    """

    __tablename__ = "trainer_availabilities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trainer_id = Column(Integer, ForeignKey("trainers.id"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)

    trainer = relationship("Trainer", back_populates="availabilities")

    def __repr__(self) -> str:
        return (
            f"<TrainerAvailability id={self.id} trainer_id={self.trainer_id} "
            f"start={self.start_time} end={self.end_time}>"
        )
