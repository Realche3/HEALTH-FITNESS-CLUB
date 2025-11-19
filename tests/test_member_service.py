"""
Tests for member-related functionality: registration, metrics, goals,
class registration, PT session scheduling, and dashboard information.
"""

from datetime import datetime, timedelta

from sqlalchemy import text

from app.services.member_service import (
    register_member,
    log_health_metric,
    create_fitness_goal,
    register_for_class,
    cancel_class_registration,
    list_member_classes,
    get_member_dashboard,
)
from app.services.admin_service import (
    create_room,
    create_class,
)
from app.services.trainer_service import (
    schedule_pt_session,
)
from models.trainer import Trainer
from app.db_utils import get_session


def _unique_email(prefix: str) -> str:
    """
    Generate a unique email address based on a prefix and timestamp.
    """
    return f"{prefix}_{int(datetime.now().timestamp())}@example.com"


def test_member_registration_and_dashboard(db_session):
    """
    Test that a member can register and that the dashboard returns
    basic information.
    """
    email = _unique_email("member_test")

    member = register_member(
        name="Test User",
        email=email,
        dob=None,
        gender=None,
        phone=None,
    )
    assert member.id is not None

    dashboard = get_member_dashboard(member.id)
    assert dashboard is not None
    assert dashboard["member_id"] == member.id
    assert dashboard["name"] == "Test User"
    assert dashboard["email"] == email


def test_health_metric_history_and_trigger_goal_completion(db_session):
    """
    Test that health metrics are logged historically and that the trigger
    completes a weight-loss goal when the target is met.
    """
    email = _unique_email("metric_test")
    member = register_member(
        name="Metric User",
        email=email,
        dob=None,
        gender=None,
        phone=None,
    )

    # Create a weight-loss goal with target_value = 80
    goal = create_fitness_goal(
        member_id=member.id,
        goal_type="weight_loss",
        target_value=80.0,
        status="active",
    )
    assert goal.status == "active"

    # Log first metric: above target
    m1 = log_health_metric(member.id, weight=85.0, heart_rate=70)
    assert m1.id is not None

    # Log second metric: meets goal
    m2 = log_health_metric(member.id, weight=79.5, heart_rate=72)
    assert m2.id is not None

    # Trigger should have updated the goal status to 'completed'
    with get_session() as db:
        refreshed_goal = db.get(type(goal), goal.id)
        assert refreshed_goal.status == "completed"


def test_class_registration_with_capacity_and_cancellation(db_session):
    """
    Test that class registration respects capacity and that cancellation works.
    """
    # Create a trainer (directly via ORM)
    with get_session() as db:
        trainer = Trainer(name="Trainer One", specialization="General")
        db.add(trainer)
        db.flush()
        trainer_id = trainer.id

    # Create a room and a class with capacity = 1
    room = create_room(name="Room A", capacity=1)
    assert room.id is not None

    schedule_time = datetime.now() + timedelta(days=1)

    gym_class = create_class(
        name="Yoga",
        capacity=1,
        trainer_id=trainer_id,
        room_id=room.id,
        schedule_time=schedule_time,
    )
    assert gym_class is not None

    # Two members
    m1 = register_member(
        name="Class User 1",
        email=_unique_email("class1"),
        dob=None,
        gender=None,
        phone=None,
    )
    m2 = register_member(
        name="Class User 2",
        email=_unique_email("class2"),
        dob=None,
        gender=None,
        phone=None,
    )

    # First registration should succeed
    assert register_for_class(m1.id, gym_class.id) is True

    # Second registration should fail due to capacity
    assert register_for_class(m2.id, gym_class.id) is False

    # Cancelling registration for m1 should succeed
    assert cancel_class_registration(m1.id, gym_class.id) is True

    # Now m2 should be able to register
    assert register_for_class(m2.id, gym_class.id) is True

    # Listing classes for m2 should include the class
    classes_for_m2 = list_member_classes(m2.id)
    assert any(c.id == gym_class.id for c in classes_for_m2)


def test_pt_session_scheduling_conflicts(db_session):
    """
    Test that PT session scheduling prevents conflicts for trainer, member,
    and room.
    """
    # Create trainer, room, and member
    with get_session() as db:
        trainer = Trainer(name="PT Trainer", specialization="PT")
        db.add(trainer)
        db.flush()
        trainer_id = trainer.id

    room = create_room(name="PT Room", capacity=2)
    member = register_member(
        name="PT Member",
        email=_unique_email("ptmember"),
        dob=None,
        gender=None,
        phone=None,
    )

    start = datetime.now() + timedelta(days=1)
    end = start + timedelta(hours=1)

    # First session: should succeed
    s1 = schedule_pt_session(
        member_id=member.id,
        trainer_id=trainer_id,
        room_id=room.id,
        start_time=start,
        end_time=end,
    )
    assert s1 is not None

    # Second session at overlapping time: should fail for same trainer/member/room
    s2 = schedule_pt_session(
        member_id=member.id,
        trainer_id=trainer_id,
        room_id=room.id,
        start_time=start + timedelta(minutes=30),
        end_time=end + timedelta(minutes=30),
    )
    assert s2 is None
