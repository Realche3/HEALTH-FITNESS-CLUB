# models/class_registration.py
"""
ClassRegistration Model
-----------------------
Represents a registration of a member to a specific group fitness class.
Used to enforce capacity rules and to track participation history.
"""

from datetime import datetime

from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from .base import Base


class ClassRegistration(Base):
    """
    ORM class for the 'class_registrations' table.

    Attributes:
        id            (int): Primary key.
        member_id     (int): FK to members.id.
        class_id      (int): FK to classes.id.
        registered_at (datetime): When the member registered for the class.

    Constraints:
        - (member_id, class_id) pair is unique so a member cannot register
          for the same class twice.

    Relationships:
        member: The Member who registered.
        gym_class: The Class the member is registered in.
    """

    __tablename__ = "class_registrations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    registered_at = Column(DateTime, nullable=False, default=datetime.now)

    member = relationship("Member", back_populates="class_registrations")
    gym_class = relationship("Class", back_populates="registrations")

    __table_args__ = (
        UniqueConstraint("member_id", "class_id", name="uq_member_class"),
    )

    def __repr__(self) -> str:
        return (
            f"<ClassRegistration id={self.id} member_id={self.member_id} "
            f"class_id={self.class_id}>"
        )
