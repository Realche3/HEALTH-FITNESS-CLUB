"""
Admin Service
-------------
Contains business logic for administrative operations such as managing rooms,
classes, equipment, and simulated billing/payments.
"""

from datetime import datetime, date
from typing import List, Optional

from sqlalchemy import select, and_, or_

from app.db_utils import get_session
from models.room import Room
from models.class_ import Class
from models.trainer import Trainer
from models.equipment import Equipment
from models.equipment_issue import EquipmentIssue
from models.payment import Payment
from models.pt_session import PTSession



# --------------------------------------------------------------------------
# ROOM MANAGEMENT
# --------------------------------------------------------------------------

def create_room(name: str, capacity: int) -> Room:
    """
    Create a new room in the fitness club.

    Args:
        name (str): Name of the room (e.g., "Yoga Studio").
        capacity (int): Maximum number of people allowed in the room.

    Returns:
        Room: The newly created Room object.
    """
    with get_session() as db:
        room = Room(name=name, capacity=capacity)
        db.add(room)
        return room


def list_rooms() -> List[Room]:
    """
    Retrieve all rooms.

    Returns:
        list[Room]: List of all Room objects.
    """
    with get_session() as db:
        result = db.execute(select(Room)).scalars().all()
        return result


# --------------------------------------------------------------------------
# CLASS MANAGEMENT
# --------------------------------------------------------------------------

def create_class(
    name: str,
    capacity: int,
    trainer_id: int,
    room_id: int,
    schedule_time: datetime,
) -> Optional[Class]:
    """
    Create a new group class.

    Performs basic checks:
        - Trainer must exist.
        - Room must exist.
        - Class capacity cannot exceed room capacity.
        - Prevents double-booking of the room at the same schedule_time.

    Args:
        name (str): Class name.
        capacity (int): Max participants for the class.
        trainer_id (int): ID of the trainer teaching the class.
        room_id (int): ID of the room where the class will be held.
        schedule_time (datetime): Date and time of the class.

    Returns:
        Class | None: Created Class object, or None if validation fails.
    """
    with get_session() as db:
        trainer = db.get(Trainer, trainer_id)
        room = db.get(Room, room_id)

        if not trainer or not room:
            # Invalid trainer or room
            return None

        if capacity > room.capacity:
            # Do not allow class capacity higher than room capacity
            return None

        # Room double-booking check: another class in same room at same time
        conflict = (
            db.query(Class)
            .filter(
                Class.room_id == room_id,
                Class.schedule_time == schedule_time,
            )
            .first()
        )
        if conflict:
            return None

        gym_class = Class(
            name=name,
            capacity=capacity,
            trainer_id=trainer_id,
            room_id=room_id,
            schedule_time=schedule_time,
        )
        db.add(gym_class)
        return gym_class


def update_class_schedule(
    class_id: int,
    new_time: datetime,
) -> Optional[Class]:
    """
    Update the scheduled time of a class.

    Args:
        class_id (int): ID of the class to update.
        new_time (datetime): New date and time.

    Returns:
        Class | None: Updated Class object, or None if not found.
    """
    with get_session() as db:
        gym_class = db.get(Class, class_id)
        if not gym_class:
            return None

        gym_class.schedule_time = new_time
        return gym_class


def change_class_room(
    class_id: int,
    new_room_id: int,
) -> Optional[Class]:
    """
    Change the room assigned to a class.

    Ensures:
        - The new room exists.
        - The new room has enough capacity for the class.
        - No double-booking of the new room at that class's schedule_time.

    Args:
        class_id (int): ID of the class to move.
        new_room_id (int): ID of the new room.

    Returns:
        Class | None: Updated Class object, or None if class/room invalid
        or capacity check / room conflict fails.
    """
    with get_session() as db:
        gym_class = db.get(Class, class_id)
        new_room = db.get(Room, new_room_id)

        if not gym_class or not new_room:
            return None

        if gym_class.capacity > new_room.capacity:
            # Cannot move if room too small
            return None

        # Check for another class in the new room at the same time
        conflict = (
            db.query(Class)
            .filter(
                Class.room_id == new_room_id,
                Class.schedule_time == gym_class.schedule_time,
                Class.id != class_id,
            )
            .first()
        )
        if conflict:
            return None

        gym_class.room_id = new_room_id
        return gym_class



def assign_trainer_to_class(
    class_id: int,
    trainer_id: int,
) -> Optional[Class]:
    """
    Assign or change the trainer for a class.

    Args:
        class_id (int): ID of the class.
        trainer_id (int): ID of the trainer.

    Returns:
        Class | None: Updated Class object, or None if class/trainer not found.
    """
    with get_session() as db:
        gym_class = db.get(Class, class_id)
        trainer = db.get(Trainer, trainer_id)

        if not gym_class or not trainer:
            return None

        gym_class.trainer_id = trainer_id
        return gym_class


def list_classes_for_day(day: date) -> List[Class]:
    """
    List all classes scheduled on a given calendar day.

    Args:
        day (date): Day to filter by.

    Returns:
        list[Class]: List of Class objects scheduled on that day.
    """
    start_dt = datetime.combine(day, datetime.min.time())
    end_dt = datetime.combine(day, datetime.max.time())

    with get_session() as db:
        query = (
            select(Class)
            .where(
                and_(
                    Class.schedule_time >= start_dt,
                    Class.schedule_time <= end_dt,
                )
            )
        )
        result = db.execute(query).scalars().all()
        return result

# --------------------------------------------------------------------------
# EQUIPMENT MANAGEMENT & MAINTENANCE
# --------------------------------------------------------------------------

def create_equipment(
    name: str,
    equipment_type: Optional[str],
    room_id: Optional[int],
    status: str = "operational",
) -> Optional[Equipment]:
    """
    Create a new equipment record and optionally assign it to a room.

    Args:
        name (str): Equipment name (e.g., "Treadmill #1").
        equipment_type (str | None): Type/category (e.g., "treadmill").
        room_id (int | None): Room ID where the equipment is located.
        status (str): Initial operational status.

    Returns:
        Equipment | None: Created Equipment object, or None if room_id invalid.
    """
    with get_session() as db:
        room = None
        if room_id is not None:
            room = db.get(Room, room_id)
            if not room:
                return None

        equipment = Equipment(
            name=name,
            type=equipment_type,
            status=status,
            room_id=room_id,
        )
        db.add(equipment)
        return equipment


def list_equipment(room_id: Optional[int] = None) -> List[Equipment]:
    """
    List equipment, optionally filtered by room.

    Args:
        room_id (int | None): If provided, only equipment in this room is returned.

    Returns:
        list[Equipment]: List of equipment records.
    """
    with get_session() as db:
        query = db.query(Equipment)
        if room_id is not None:
            query = query.filter(Equipment.room_id == room_id)
        return query.all()


def log_equipment_issue(equipment_id: int, description: str) -> Optional[EquipmentIssue]:
    """
    Log a new maintenance issue for a given piece of equipment.

    Args:
        equipment_id (int): ID of the equipment.
        description (str): Description of the problem.

    Returns:
        EquipmentIssue | None: Created issue, or None if equipment not found.
    """
    with get_session() as db:
        equipment = db.get(Equipment, equipment_id)
        if not equipment:
            return None

        issue = EquipmentIssue(
            equipment_id=equipment_id,
            description=description,
            status="open",
        )
        db.add(issue)
        # Optionally mark equipment as out of order
        equipment.status = "out_of_order"
        return issue


def update_equipment_issue_status(
    issue_id: int,
    new_status: str,
) -> Optional[EquipmentIssue]:
    """
    Update the status of an equipment issue. If the issue is resolved,
    the resolved_at timestamp is set and the equipment status can be
    marked back to 'operational'.

    Args:
        issue_id (int): ID of the EquipmentIssue.
        new_status (str): New status (e.g., "in_progress", "resolved").

    Returns:
        EquipmentIssue | None: Updated issue or None if not found.
    """
    with get_session() as db:
        issue = db.get(EquipmentIssue, issue_id)
        if not issue:
            return None

        issue.status = new_status

        if new_status == "resolved":
            issue.resolved_at = datetime.now()
            # Optionally set equipment back to operational
            equipment = issue.equipment
            if equipment and equipment.status != "operational":
                equipment.status = "operational"

        return issue


def list_equipment_issues(
    room_id: Optional[int] = None,
    status: Optional[str] = None,
) -> List[EquipmentIssue]:
    """
    List equipment issues, optionally filtered by room and/or status.

    Args:
        room_id (int | None): Only issues for equipment in this room.
        status  (str | None): Only issues with this status.

    Returns:
        list[EquipmentIssue]: Matching issue records.
    """
    with get_session() as db:
        query = db.query(EquipmentIssue).join(Equipment)

        if room_id is not None:
            query = query.filter(Equipment.room_id == room_id)

        if status is not None:
            query = query.filter(EquipmentIssue.status == status)

        return query.all()

# --------------------------------------------------------------------------
# BILLING & PAYMENT (SIMULATED)
# --------------------------------------------------------------------------

def create_member_payment(
    member_id: int,
    amount: float,
    method: str,
    status: str = "pending",
) -> Optional[Payment]:
    """
    Create a payment record for a member, simulating an invoice/payment
    entry. The status can later be updated (e.g., 'pending' -> 'completed').

    Args:
        member_id (int): ID of the member.
        amount (float): Amount due or paid.
        method (str): Payment method (e.g., 'cash', 'credit').
        status (str): Initial status (e.g., 'pending', 'completed').

    Returns:
        Payment | None: Created Payment or None if member not found.
    """
    with get_session() as db:
        # We don't strictly need to fetch Member, but we can validate ID
        from models.member import Member  # local import to avoid cycles

        member = db.get(Member, member_id)
        if not member:
            return None

        payment = Payment(
            member_id=member_id,
            amount=amount,
            method=method,
            status=status,
            created_at=datetime.now(),
        )
        db.add(payment)
        return payment


def update_payment_status(payment_id: int, new_status: str) -> Optional[Payment]:
    """
    Update the status of an existing payment (e.g., to simulate an invoice
    being paid or refunded).

    Args:
        payment_id (int): ID of the payment record.
        new_status (str): New status value.

    Returns:
        Payment | None: Updated Payment or None if not found.
    """
    with get_session() as db:
        payment = db.get(Payment, payment_id)
        if not payment:
            return None

        payment.status = new_status
        return payment


def list_member_payments(member_id: int) -> List[Payment]:
    """
    List all payments associated with a given member.

    Args:
        member_id (int): ID of the member.

    Returns:
        list[Payment]: List of payment records.
    """
    with get_session() as db:
        payments = (
            db.query(Payment)
            .filter(Payment.member_id == member_id)
            .order_by(Payment.created_at.desc())
            .all()
        )
        return payments
