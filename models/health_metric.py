"""
HealthMetric Model
------------------
Represents a single health measurement recorded by a member (weight,
heart rate, etc.).
"""

from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


class HealthMetric(Base):
    """
    ORM class for the 'health_metrics' table.

    Attributes:
        id         (int): Primary key.
        member_id  (int): FK to members.id.
        weight     (float): Weight in kg.
        heart_rate (int): Heart rate in bpm.
        timestamp  (datetime): When the measurement was recorded.

    Relationships:
        member: The member who recorded this metric.
    """

    __tablename__ = "health_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    weight = Column(Float)
    heart_rate = Column(Integer)
    timestamp = Column(DateTime, nullable=False)

    member = relationship("Member", back_populates="health_metrics")

    def __repr__(self) -> str:
        return f"<HealthMetric id={self.id} member_id={self.member_id}>"
