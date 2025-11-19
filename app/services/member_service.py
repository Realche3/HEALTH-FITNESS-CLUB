"""
Member Service
--------------
Contains business logic for member operations such as creating accounts,
logging health metrics, managing fitness goals, and viewing member data.
"""

from datetime import datetime
from app.db_utils import get_session
from models.member import Member
from models.health_metric import HealthMetric
from models.fitness_goal import FitnessGoal
from models.payment import Payment


# --------------------------------------------------------------------------
# MEMBER REGISTRATION
# --------------------------------------------------------------------------

def register_member(name: str, email: str, dob=None, gender=None, phone=None):
    """
    Create a new member record.

    Args:
        name (str): Member's full name.
        email (str): Unique email address.
        dob (date | None): Date of birth.
        gender (str | None): Gender.
        phone (str | None): Phone number.

    Returns:
        Member: The newly created Member object.
    """
    with get_session() as db:
        member = Member(
            name=name,
            email=email,
            dob=dob,
            gender=gender,
            phone=phone,
        )
        db.add(member)
        return member


# --------------------------------------------------------------------------
# UPDATE MEMBER INFO
# --------------------------------------------------------------------------

def update_member(member_id: int, **kwargs):
    """
    Update member fields such as phone, gender, or name.

    Allowed kwargs:
        name, email, dob, gender, phone

    Returns:
        Member | None: Updated member or None if not found.
    """
    with get_session() as db:
        member = db.get(Member, member_id)
        if not member:
            return None

        for key, value in kwargs.items():
            if hasattr(member, key):
                setattr(member, key, value)

        return member


# --------------------------------------------------------------------------
# LOG HEALTH METRIC
# --------------------------------------------------------------------------

def log_health_metric(member_id: int, weight: float = None, heart_rate: int = None):
    """
    Add a new health metric entry for a member.

    Args:
        member_id (int): FK to Member.
        weight (float | None)
        heart_rate (int | None)

    Returns:
        HealthMetric
    """
    with get_session() as db:
        metric = HealthMetric(
            member_id=member_id,
            weight=weight,
            heart_rate=heart_rate,
            timestamp=datetime.now(),
        )
        db.add(metric)
        return metric


# --------------------------------------------------------------------------
# CREATE FITNESS GOAL
# --------------------------------------------------------------------------

def create_fitness_goal(member_id: int, goal_type: str, target_value: float, status="active"):
    """
    Create a new fitness goal for the member.

    Args:
        member_id (int)
        goal_type (str)
        target_value (float)
        status (str)

    Returns:
        FitnessGoal
    """
    with get_session() as db:
        goal = FitnessGoal(
            member_id=member_id,
            goal_type=goal_type,
            target_value=target_value,
            status=status,
        )
        db.add(goal)
        return goal


# --------------------------------------------------------------------------
# RECORD PAYMENT
# --------------------------------------------------------------------------

def record_payment(member_id: int, amount: float, method: str, status="completed"):
    """
    Insert a new payment record.

    Args:
        member_id (int)
        amount (float)
        method (str)
        status (str)

    Returns:
        Payment
    """
    with get_session() as db:
        payment = Payment(
            member_id=member_id,
            amount=amount,
            method=method,
            status=status,
            created_at=datetime.now(),
        )
        db.add(payment)
        return payment


# --------------------------------------------------------------------------
# GET MEMBER DETAILS
# --------------------------------------------------------------------------

def get_member_profile(member_id: int):
    """
    Retrieve a member and all related info.

    Returns:
        dict | None
    """
    with get_session() as db:
        member = db.get(Member, member_id)
        if not member:
            return None

        return {
            "id": member.id,
            "name": member.name,
            "email": member.email,
            "phone": member.phone,
            "goals": [g.goal_type for g in member.goals],
            "metrics": len(member.health_metrics),
            "payments": len(member.payments),
        }
