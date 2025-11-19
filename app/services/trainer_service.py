"""
Trainer Service
---------------
Contains business logic related to trainers, including managing personal
training sessions, availability, and limited read-only access to member data.
"""

from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import and_, or_, select, func

from app.db_utils import get_session
from models.trainer import Trainer
from models.pt_session import PTSession
from models.class_ import Class
from models.room import Room
from models.trainer_availability import TrainerAvailability
from models.member import Member
from models.fitness_goal import FitnessGoal
from models.health_metric import HealthMetric
from models.class_registration import ClassRegistration




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
# TRAINER AVAILABILITY MANAGEMENT
# --------------------------------------------------------------------------

def set_availability(
    trainer_id: int,
    start_time: datetime,
    end_time: datetime,
) -> Optional[TrainerAvailability]:
    """
    Define a new availability window for a trainer, ensuring no overlapping
    intervals for the same trainer.

    Business rules:
        - Trainer must exist.
        - start_time < end_time.
        - No overlap with existing availability windows for that trainer.
          Overlap condition:
              existing.start < new_end AND existing.end > new_start

    Args:
        trainer_id (int): ID of the trainer.
        start_time (datetime): Start of availability window.
        end_time (datetime): End of availability window.

    Returns:
        TrainerAvailability | None: Created availability object if successful,
        or None if validation fails.
    """
    if start_time >= end_time:
        return None

    with get_session() as db:
        trainer = db.get(Trainer, trainer_id)
        if not trainer:
            return None

        # Check for overlapping availabilities
        conflict_q = (
            select(TrainerAvailability)
            .where(TrainerAvailability.trainer_id == trainer_id)
            .where(TrainerAvailability.start_time < end_time)
            .where(TrainerAvailability.end_time > start_time)
        )
        conflict = db.execute(conflict_q).scalars().first()
        if conflict:
            return None

        availability = TrainerAvailability(
            trainer_id=trainer_id,
            start_time=start_time,
            end_time=end_time,
        )
        db.add(availability)
        return availability


def list_availability(trainer_id: int) -> List[TrainerAvailability]:
    """
    List all availability windows for a given trainer.

    Args:
        trainer_id (int): ID of the trainer.

    Returns:
        list[TrainerAvailability]: All availability entries for the trainer.
    """
    with get_session() as db:
        result = (
            db.query(TrainerAvailability)
            .filter(TrainerAvailability.trainer_id == trainer_id)
            .order_by(TrainerAvailability.start_time.asc())
            .all()
        )
        return result


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
# --------------------------------------------------------------------------
# MEMBER LOOKUP (READ-ONLY, TRAINER-SPECIFIC)
# --------------------------------------------------------------------------

def member_lookup_for_trainer(trainer_id: int, name_query: str) -> List[dict]:
    """
    Search for members assigned to a given trainer by name (case-insensitive),
    and return limited read-only information:

        - member_id
        - name
        - email
        - latest health metric (weight, heart_rate, timestamp)
        - current active goals

    Only members who are "assigned" to the trainer are included. For this
    implementation, a member is considered assigned if:
        - They have at least one PTSession with this trainer, OR
        - They are registered in at least one Class taught by this trainer.

    Args:
        trainer_id (int): ID of the trainer performing the lookup.
        name_query (str): Case-insensitive substring to match against member names.

    Returns:
        list[dict]: List of member summary dictionaries.
    """
    with get_session() as db:
        # Subquery: members from PT sessions with this trainer
        pt_member_subq = (
            select(PTSession.member_id)
            .where(PTSession.trainer_id == trainer_id)
        )

        # Subquery: members from classes taught by this trainer
        class_member_subq = (
            select(ClassRegistration.member_id)
            .join(Class, ClassRegistration.class_id == Class.id)
            .where(Class.trainer_id == trainer_id)
        )

        # Union of both sets of member_ids
        assigned_member_ids_subq = pt_member_subq.union(class_member_subq).subquery()

        # Main member query: only assigned members, filter by name (case-insensitive)
        members = (
            db.query(Member)
            .filter(Member.id.in_(select(assigned_member_ids_subq.c.member_id)))
            .filter(Member.name.ilike(f"%{name_query}%"))
            .all()
        )

        results: List[dict] = []

        for m in members:
            # Latest health metric
            latest_metric = (
                db.query(HealthMetric)
                .filter(HealthMetric.member_id == m.id)
                .order_by(HealthMetric.timestamp.desc())
                .first()
            )
            latest_metric_data = None
            if latest_metric:
                latest_metric_data = {
                    "weight": latest_metric.weight,
                    "heart_rate": latest_metric.heart_rate,
                    "timestamp": latest_metric.timestamp,
                }

            # Active goals
            active_goals = (
                db.query(FitnessGoal)
                .filter(
                    FitnessGoal.member_id == m.id,
                    FitnessGoal.status == "active",
                )
                .all()
            )
            active_goals_data = [
                {
                    "id": g.id,
                    "goal_type": g.goal_type,
                    "target_value": g.target_value,
                    "status": g.status,
                }
                for g in active_goals
            ]

            results.append(
                {
                    "member_id": m.id,
                    "name": m.name,
                    "email": m.email,
                    "latest_metric": latest_metric_data,
                    "active_goals": active_goals_data,
                }
            )

        return results
