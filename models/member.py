"""
Member Model
------------
Represents a gym member. Members can log health metrics, set fitness goals,
schedule personal training sessions, and make payments.
"""

from sqlalchemy import Column, Integer, String, Date, Index
from sqlalchemy.orm import relationship
from .base import Base


class Member(Base):
    """
    ORM class for the 'members' table.

    Attributes:
        id          (int): Primary key.
        name        (str): Full name of the member.
        dob         (date): Date of birth.
        gender      (str): Gender of member.
        email       (str): Unique email address for login/identification.
        phone       (str): Phone number.

    Relationships:
        health_metrics: List of HealthMetric entries.
        goals: List of FitnessGoal entries.
        sessions: List of PTSession entries.
        payments: List of Payment records.
    """

    __tablename__ = "members"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    dob = Column(Date)
    gender = Column(String)
    email = Column(String, unique=True, nullable=False)
    phone = Column(String)

    # Relationships
    health_metrics = relationship(
        "HealthMetric",
        back_populates="member",
        cascade="all, delete-orphan",
    )
    goals = relationship(
        "FitnessGoal",
        back_populates="member",
        cascade="all, delete-orphan",
    )
    sessions = relationship(
        "PTSession",
        back_populates="member",
        cascade="all, delete-orphan",
    )
    payments = relationship(
        "Payment",
        back_populates="member",
        cascade="all, delete-orphan",
    )

    # Explicit index requirement for COMP3005
    __table_args__ = (
        Index("ix_members_email", "email"),
    )

    def __repr__(self) -> str:
        return f"<Member id={self.id} name={self.name!r} email={self.email!r}>"
