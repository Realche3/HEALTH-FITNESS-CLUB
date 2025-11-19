"""
Trainer Service
---------------
Contains business logic related to trainers, including managing personal
training sessions and viewing trainer schedules.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import and_, select

from app.db_utils import get_session
from models.trainer import Trainer
from models.pt_session import PTSession
from models.class_ import Class
from models.room import Room


def get_trainer(trainer_id: int) -> Optional[Trainer]:
    """
    Retrieve a trainer by ID.

    Args:
        trainer_id (int): ID of the trainer.

    Returns:
        Trainer | None: Trainer object or None if not found.
    """
    with get_session() as db:
        return db.get(Trainer, trainer_id)


# --------------------------------------------------------------------------
# PT SESSION MANAGEMENT
# --------------------------------------------------------------------------

def schedule_pt_session(
    member_id: int,
    trainer_id: int,
    room_id: Optional[int],
    start_time: datetime,
    end_time: Optional[datetime],
    status: str = "scheduled",
) -> Optional[PTSession]:
    """
    Schedule a new personal training session.

    This function also checks for basic time conflicts:
    - The trainer cannot have another PT session overlapping this time.
    - The room (if provided) cannot be used in another PT session at that time.

    Args:
        member_id (int): Member who books the session.
        trainer_id (int): Trainer conducting the session.
        room_id (int | None): Room used for the session (can be None).
        start_time (datetime): Session start time.
        end_time (datetime | None): Session end time.
        status (str): Initial status (default: "scheduled").

    Returns:
        PTSession | None: The created PTSession, or None if conflict detected.
    """
    with get_session() as db:
        # Basic trainer conflict check
        conflict_query = select(PTSession).where(
            PTSession.trainer_id == trainer_id,
            PTSession.start_time == start_time,
        )
        conflict = db.execute(conflict_query).scalars().first()
        if conflict:
            # Conflict detected, do not create
            return None

        # Optional room conflict check
        if room_id is not None:
            room_conflict_query = select(PTSession).where(
                PTSession.room_id == room_id,
                PTSession.start_time == start_time,
            )
            room_conflict = db.execute(room_conflict_query).scalars().first()
            if room_conflict:
                return None

        session = PTSession(
            member_id=member_id,
            trainer_id=trainer_id,
            room_id=room_id,
            start_time=start_time,
            end_time=end_time,
            status=status,
        )
        db.add(session)
        return session


def update_pt_session_status(session_id: int, status: str) -> Optional[PTSession]:
    """
    Update the status of an existing PT session.

    Common statuses:
        - "scheduled"
        - "completed"
        - "cancelled"

    Args:
        session_id (int): ID of the PTSession.
        status (str): New status value.

    Returns:
        PTSession | None: Updated session or None if not found.
    """
    with get_session() as db:
        session = db.get(PTSession, session_id)
        if not session:
            return None

        session.status = status
        return session


def move_pt_session_to_room(session_id: int, new_room_id: int) -> Optional[PTSession]:
    """
    Change the room for a PT session.

    Args:
        session_id (int): ID of the session to update.
        new_room_id (int): ID of the new room.

    Returns:
        PTSession | None: Updated session or None if not found.
    """
    with get_session() as db:
        session = db.get(PTSession, session_id)
        if not session:
            return None

        room = db.get(Room, new_room_id)
        if not room:
            return None

        session.room_id = new_room_id
        return session


def list_trainer_sessions(
    trainer_id: int,
    status: Optional[str] = None,
) -> List[PTSession]:
    """
    Return all PT sessions for a given trainer, optionally filtered by status.

    Args:
        trainer_id (int): ID of the trainer.
        status (str | None): Optional status filter.

    Returns:
        list[PTSession]: List of matching PTSession objects.
    """
    with get_session() as db:
        query = select(PTSession).where(PTSession.trainer_id == trainer_id)
        if status:
            query = query.where(PTSession.status == status)

        result = db.execute(query).scalars().all()
        return result


# --------------------------------------------------------------------------
# TRAINER SCHEDULE (CLASSES + PT SESSIONS)
# --------------------------------------------------------------------------

def get_trainer_schedule(
    trainer_id: int,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> dict:
    """
    Get a trainer's schedule (classes and PT sessions) within an optional
    time window.

    Args:
        trainer_id (int): ID of the trainer.
        start (datetime | None): Start of time range (inclusive).
        end (datetime | None): End of time range (inclusive).

    Returns:
        dict: {
            "trainer_id": int,
            "classes": [Class, ...],
            "pt_sessions": [PTSession, ...],
        }
    """
    with get_session() as db:
        # Classes
        class_query = select(Class).where(Class.trainer_id == trainer_id)
        if start:
            class_query = class_query.where(Class.schedule_time >= start)
        if end:
            class_query = class_query.where(Class.schedule_time <= end)

        classes = db.execute(class_query).scalars().all()

        # PT sessions
        session_query = select(PTSession).where(PTSession.trainer_id == trainer_id)
        if start:
            session_query = session_query.where(PTSession.start_time >= start)
        if end:
            session_query = session_query.where(PTSession.start_time <= end)

        sessions = db.execute(session_query).scalars().all()

        return {
            "trainer_id": trainer_id,
            "classes": classes,
            "pt_sessions": sessions,
        }
