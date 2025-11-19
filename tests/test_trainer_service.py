"""
Tests for trainer-related functionality: availability, schedule view,
and read-only member lookup.
"""

from datetime import datetime, timedelta

from app.services.trainer_service import (
    set_availability,
    list_availability,
    get_trainer_schedule,
    member_lookup_for_trainer,
    schedule_pt_session,
)
from app.services.member_service import register_member
from app.services.admin_service import create_room, create_class
from models.trainer import Trainer
from app.db_utils import get_session


def test_trainer_availability_non_overlapping(db_session):
    """
    Test that trainer availability entries cannot overlap.
    """
    with get_session() as db:
        trainer = Trainer(name="Avail Trainer", specialization="Cardio")
        db.add(trainer)
        db.flush()
        trainer_id = trainer.id

    start1 = datetime.now() + timedelta(days=1, hours=9)
    end1 = start1 + timedelta(hours=2)

    slot1 = set_availability(trainer_id, start1, end1)
    assert slot1 is not None

    # Overlapping slot should fail
    start2 = start1 + timedelta(hours=1)
    end2 = start2 + timedelta(hours=2)
    slot2 = set_availability(trainer_id, start2, end2)
    assert slot2 is None

    # Non-overlapping after previous end should succeed
    start3 = end1 + timedelta(hours=1)
    end3 = start3 + timedelta(hours=2)
    slot3 = set_availability(trainer_id, start3, end3)
    assert slot3 is not None

    slots = list_availability(trainer_id)
    assert len(slots) >= 2


def test_trainer_schedule_and_member_lookup(db_session):
    """
    Test that a trainer can view a schedule and lookup assigned members.
    """
    with get_session() as db:
        trainer = Trainer(name="Schedule Trainer", specialization="Strength")
        db.add(trainer)
        db.flush()
        trainer_id = trainer.id

    room = create_room(name="Schedule Room", capacity=5)
    assert room.id is not None

    # Create member and assign via PT session and class
    member = register_member(
        name="Lookup Member",
        email=f"lookup_{int(datetime.now().timestamp())}@example.com",
        dob=None,
        gender=None,
        phone=None,
    )

    # PT session
    pt_start = datetime.now() + timedelta(days=1)
    schedule_pt_session(
        member_id=member.id,
        trainer_id=trainer_id,
        room_id=room.id,
        start_time=pt_start,
        end_time=pt_start + timedelta(hours=1),
    )

    # Class
    class_time = datetime.now() + timedelta(days=2)
    gym_class = create_class(
        name="Strength Class",
        capacity=5,
        trainer_id=trainer_id,
        room_id=room.id,
        schedule_time=class_time,
    )
    assert gym_class is not None

    # Schedule should have at least one PT session and one class
    schedule = get_trainer_schedule(trainer_id, start=datetime.now(), end=None)
    assert len(schedule["classes"]) >= 1
    assert len(schedule["pt_sessions"]) >= 1

    # Member lookup should return the created member when searching by name
    results = member_lookup_for_trainer(trainer_id, "Lookup")
    assert any(r["member_id"] == member.id for r in results)
