"""
Member Service
--------------
Contains business logic for member operations such as creating accounts,
logging health metrics, managing fitness goals, and viewing member data.
"""
from typing import List

from datetime import datetime
from app.db_utils import get_session
from models.member import Member
from models.health_metric import HealthMetric
from models.fitness_goal import FitnessGoal
from models.payment import Payment
from models.class_registration import ClassRegistration


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


# --------------------------------------------------------------------------
# GROUP CLASS REGISTRATION
# --------------------------------------------------------------------------

def register_for_class(member_id: int, class_id: int) -> bool:
    """
    Register a member for a group fitness class if capacity allows.

    Business rules:
        - Class must exist.
        - Member must exist.
        - Member cannot register for the same class twice.
        - Class cannot exceed its capacity (based on registrations count).

    Args:
        member_id (int): ID of the member.
        class_id (int): ID of the class.

    Returns:
        bool: True if registration succeeded, False otherwise.
    """
    with get_session() as db:
        member = db.get(Member, member_id)
        gym_class = db.get(Class, class_id)

        if not member or not gym_class:
            return False

        # Check if already registered
        existing = (
            db.query(ClassRegistration)
            .filter(
                ClassRegistration.member_id == member_id,
                ClassRegistration.class_id == class_id,
            )
            .first()
        )
        if existing:
            return False

        # Check capacity
        current_count = (
            db.query(ClassRegistration)
            .filter(ClassRegistration.class_id == class_id)
            .count()
        )
        if current_count >= gym_class.capacity:
            return False

        registration = ClassRegistration(
            member_id=member_id,
            class_id=class_id,
            registered_at=datetime.now(),
        )
        db.add(registration)
        return True


def cancel_class_registration(member_id: int, class_id: int) -> bool:
    """
    Cancel an existing class registration for a member.

    Args:
        member_id (int): ID of the member.
        class_id (int): ID of the class.

    Returns:
        bool: True if a registration was found and deleted, False otherwise.
    """
    with get_session() as db:
        registration = (
            db.query(ClassRegistration)
            .filter(
                ClassRegistration.member_id == member_id,
                ClassRegistration.class_id == class_id,
            )
            .first()
        )
        if not registration:
            return False

        db.delete(registration)
        return True


def list_member_classes(member_id: int) -> List[Class]:
    """
    List all classes a member is registered for.

    Args:
        member_id (int): ID of the member.

    Returns:
        list[Class]: All classes the member is currently registered in.
    """
    with get_session() as db:
        registrations = (
            db.query(ClassRegistration)
            .filter(ClassRegistration.member_id == member_id)
            .all()
        )
        class_ids = [r.class_id for r in registrations]

        if not class_ids:
            return []

        classes = db.query(Class).filter(Class.id.in_(class_ids)).all()
        return classes
