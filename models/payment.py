"""
Payment Model
-------------
Represents a financial transaction made by a member, such as membership
payments or class fees.
"""

from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


class Payment(Base):
    """
    ORM class for the 'payments' table.

    Attributes:
        id         (int): Primary key.
        member_id  (int): FK to members.id.
        amount     (float): Payment amount.
        status     (str): Payment status (pending, completed, etc.).
        method     (str): Payment method (credit, debit, cash).
        created_at (datetime): Timestamp of the payment.

    Relationships:
        member: The member who made the payment.
    """

    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String, nullable=False)
    method = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)

    member = relationship("Member", back_populates="payments")

    def __repr__(self) -> str:
        return f"<Payment id={self.id} member_id={self.member_id} amount={self.amount}>"
