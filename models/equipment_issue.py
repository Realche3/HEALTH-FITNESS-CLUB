# models/equipment_issue.py
"""
EquipmentIssue Model
--------------------
Represents a maintenance issue reported for a specific piece of equipment.
Admins can log new issues, update their status (e.g., open, in_progress,
resolved), and track when issues were created/resolved.
"""

from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base


class EquipmentIssue(Base):
    """
    ORM class for the 'equipment_issues' table.

    Attributes:
        id           (int): Primary key.
        equipment_id (int): FK to equipment.id.
        description  (str): Text describing the issue.
        status       (str): Issue status ("open", "in_progress", "resolved").
        created_at   (datetime): When the issue was created.
        resolved_at  (datetime | None): When the issue was resolved (optional).

    Relationships:
        equipment: The Equipment this issue refers to.
    """

    __tablename__ = "equipment_issues"

    id = Column(Integer, primary_key=True, autoincrement=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=False)
    description = Column(String, nullable=False)
    status = Column(String, nullable=False, default="open")
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    resolved_at = Column(DateTime, nullable=True)

    equipment = relationship("Equipment", back_populates="issues")

    def __repr__(self) -> str:
        return (
            f"<EquipmentIssue id={self.id} equipment_id={self.equipment_id} "
            f"status={self.status!r}>"
        )
