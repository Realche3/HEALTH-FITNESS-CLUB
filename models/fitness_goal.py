"""
FitnessGoal Model
-----------------
Represents a specific fitness goal set by a member, such as weight loss,
muscle gain, or achieving a target metric.
"""

from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


class FitnessGoal(Base):
    """
    ORM class for the 'fitness_goals' table.

    Attributes:
        id           (int): Primary key.
        member_id    (int): FK to members.id.
        goal_type    (str): Type of goal (e.g., "weight loss").
        target_value (float): Target metric value.
        status       (str): Status (active, completed, etc.).

    Relationships:
        member: The member who owns this goal.
    """

    __tablename__ = "fitness_goals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    goal_type = Column(String, nullable=False)
    target_value = Column(Float)
    status = Column(String, nullable=False)

    member = relationship("Member", back_populates="goals")

    def __repr__(self) -> str:
        return f"<FitnessGoal id={self.id} member_id={self.member_id}>"
