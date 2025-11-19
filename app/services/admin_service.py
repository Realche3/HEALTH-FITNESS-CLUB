"""
Admin Service
-------------
Contains business logic for administrative operations such as managing rooms,
creating and updating classes, and assigning trainers/rooms.

These functions are intended to be used by an "admin" role in the system.
"""

from datetime import datetime, date
from typing import List, Optional

from sqlalchemy import select, and_

from app.db_utils import get_session
from models.room import Room
from models.class_ import Class
from models.trainer import Trainer


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

    Ensures the new room exists and has enough capacity for the class.

    Args:
        class_id (int): ID of the class to move.
        new_room_id (int): ID of the new room.

    Returns:
        Class | None: Updated Class object, or None if class/room invalid
        or capacity check fails.
    """
    with get_session() as db:
        gym_class = db.get(Class, class_id)
        new_room = db.get(Room, new_room_id)

        if not gym_class or not new_room:
            return None

        if gym_class.capacity > new_room.capacity:
            # Cannot move if room too small
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
