"""
Trainer Service
---------------
Contains business logic related to trainers, including managing personal
training sessions and viewing trainer schedules.
"""

from datetime import datetime, timedelta
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

    This function enforces the following business rules:
        - Trainer cannot have overlapping PT sessions.
        - Member cannot have overlapping PT sessions.
        - Room (if specified) cannot host overlapping PT sessions.
        - Basic overlap is defined as:
              existing.start < new_end AND existing.end > new_start
          (with NULL end_time treated as 1 hour after start).

    Args:
        member_id (int): Member who books the session.
        trainer_id (int): Trainer conducting the session.
        room_id (int | None): Room used for the session (can be None).
        start_time (datetime): Session start time.
        end_time (datetime | None): Session end time. If None, a default
            duration of 1 hour is assumed for conflict checks.
        status (str): Initial status (default: "scheduled").

    Returns:
        PTSession | None: The created PTSession, or None if a conflict is detected.
    """
    # Assume default 1-hour session if end_time is not provided
    if end_time is None:
        end_time = start_time + timedelta(hours=1)

    with get_session() as db:
        # Helper subquery for overlap condition
        def overlap_filter(query):
            return query.where(
                PTSession.start_time < end_time,
                or_(
                    PTSession.end_time.is_(None),
                    PTSession.end_time > start_time,
                ),
                PTSession.status != "cancelled",
            )

        # Trainer conflict
        trainer_conflict_q = select(PTSession).where(PTSession.trainer_id == trainer_id)
        trainer_conflict_q = overlap_filter(trainer_conflict_q)
        trainer_conflict = db.execute(trainer_conflict_q).scalars().first()
        if trainer_conflict:
            return None

        # Member conflict
        member_conflict_q = select(PTSession).where(PTSession.member_id == member_id)
        member_conflict_q = overlap_filter(member_conflict_q)
        member_conflict = db.execute(member_conflict_q).scalars().first()
        if member_conflict:
            return None

        # Room conflict (only if room specified)
        if room_id is not None:
            room_conflict_q = select(PTSession).where(PTSession.room_id == room_id)
            room_conflict_q = overlap_filter(room_conflict_q)
            room_conflict = db.execute(room_conflict_q).scalars().first()
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

def reschedule_pt_session(
    session_id: int,
    new_start_time: datetime,
    new_end_time: Optional[datetime],
) -> Optional[PTSession]:
    """
    Reschedule an existing PT session to a new time window.

    Enforces the same conflict rules as schedule_pt_session(), but ignores
    the session itself when checking for overlaps.

    Args:
        session_id (int): ID of the PTSession to move.
        new_start_time (datetime): New start time.
        new_end_time (datetime | None): New end time. If None, assumes 1 hour.

    Returns:
        PTSession | None: Updated session if successful, or None if conflicts
        or session not found / cancelled.
    """
    if new_end_time is None:
        new_end_time = new_start_time + timedelta(hours=1)

    with get_session() as db:
        session = db.get(PTSession, session_id)
        if not session or session.status == "cancelled":
            return None

        member_id = session.member_id
        trainer_id = session.trainer_id
        room_id = session.room_id

        def overlap_filter(query):
            return query.where(
                PTSession.start_time < new_end_time,
                or_(
                    PTSession.end_time.is_(None),
                    PTSession.end_time > new_start_time,
                ),
                PTSession.status != "cancelled",
                PTSession.id != session_id,  # ignore self
            )

        # Trainer conflict
        trainer_conflict_q = select(PTSession).where(PTSession.trainer_id == trainer_id)
        trainer_conflict_q = overlap_filter(trainer_conflict_q)
        if db.execute(trainer_conflict_q).scalars().first():
            return None

        # Member conflict
        member_conflict_q = select(PTSession).where(PTSession.member_id == member_id)
        member_conflict_q = overlap_filter(member_conflict_q)
        if db.execute(member_conflict_q).scalars().first():
            return None

        # Room conflict
        if room_id is not None:
            room_conflict_q = select(PTSession).where(PTSession.room_id == room_id)
            room_conflict_q = overlap_filter(room_conflict_q)
            if db.execute(room_conflict_q).scalars().first():
                return None

        # No conflicts: apply changes
        session.start_time = new_start_time
        session.end_time = new_end_time
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
