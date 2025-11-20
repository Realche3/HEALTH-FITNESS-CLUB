"""
Seed Data Script
----------------
Utility script to populate the Health & Fitness Club database with
sample data for testing and demonstration.

This script:
    - Creates rooms
    - Creates trainers and availability
    - Creates members
    - Logs health metrics and fitness goals
    - Schedules classes and registers members
    - Schedules PT sessions
    - Creates equipment and issues
    - Creates payments

Usage:
    From the project root (virtualenv activated):

        python -m app.seed_data

Note:
    This script uses raw ORM operations via the get_session() context
    manager and does not implement any CLI interaction.
"""

from datetime import datetime, date, timedelta

from app.db_utils import get_session
from models.member import Member
from models.trainer import Trainer
from models.room import Room
from models.class_ import Class
from models.class_registration import ClassRegistration
from models.pt_session import PTSession
from models.trainer_availability import TrainerAvailability
from models.health_metric import HealthMetric
from models.fitness_goal import FitnessGoal
from models.payment import Payment
from models.equipment import Equipment
from models.equipment_issue import EquipmentIssue


def seed_data() -> None:
    """
    Populate the database with a small but complete set of data
    demonstrating all major relationships.
    """
    print("Seeding database with sample data ...")

    with get_session() as db:
        # --------------------------------------------------------------
        # Rooms
        # --------------------------------------------------------------
        room1 = Room(name="Studio A", capacity=15)
        room2 = Room(name="Studio B", capacity=10)
        room3 = Room(name="PT Room 1", capacity=2)

        db.add_all([room1, room2, room3])
        db.flush()
        print(f"Created rooms: {room1.id}, {room2.id}, {room3.id}")

        # --------------------------------------------------------------
        # Trainers
        # --------------------------------------------------------------
        t1 = Trainer(name="Alice Trainer", specialization="Strength")
        t2 = Trainer(name="Bob Coach", specialization="Cardio")
        t3 = Trainer(name="Charlie PT", specialization="Personal Training")

        db.add_all([t1, t2, t3])
        db.flush()
        print(f"Created trainers: {t1.id}, {t2.id}, {t3.id}")

        # --------------------------------------------------------------
        # Trainer Availability
        # --------------------------------------------------------------
        av1 = TrainerAvailability(
            trainer_id=t1.id,
            start_time=datetime(2025, 12, 1, 9, 0),
            end_time=datetime(2025, 12, 1, 12, 0),
        )
        av2 = TrainerAvailability(
            trainer_id=t3.id,
            start_time=datetime(2025, 12, 1, 13, 0),
            end_time=datetime(2025, 12, 1, 17, 0),
        )
        db.add_all([av1, av2])

        # --------------------------------------------------------------
        # Members
        # --------------------------------------------------------------
        m1 = Member(
            name="John Member",
            email="john@example.com",
            dob=date(1995, 5, 10),
            gender="M",
            phone="555-1111",
        )
        m2 = Member(
            name="Sarah Client",
            email="sarah@example.com",
            dob=date(1998, 8, 21),
            gender="F",
            phone="555-2222",
        )
        m3 = Member(
            name="David User",
            email="david@example.com",
            dob=date(1990, 1, 2),
            gender="M",
            phone="555-3333",
        )

        db.add_all([m1, m2, m3])
        db.flush()
        print(f"Created members: {m1.id}, {m2.id}, {m3.id}")

        # --------------------------------------------------------------
        # Health Metrics & Fitness Goals
        # --------------------------------------------------------------
        hm1 = HealthMetric(
            member_id=m1.id,
            weight=85.0,
            heart_rate=72,
            timestamp=datetime(2025, 11, 1, 10, 0),
        )
        hm2 = HealthMetric(
            member_id=m1.id,
            weight=82.5,
            heart_rate=70,
            timestamp=datetime(2025, 11, 15, 10, 0),
        )
        hm3 = HealthMetric(
            member_id=m2.id,
            weight=68.0,
            heart_rate=65,
            timestamp=datetime(2025, 11, 10, 9, 30),
        )

        db.add_all([hm1, hm2, hm3])

        goal1 = FitnessGoal(
            member_id=m1.id,
            goal_type="weight_loss",
            target_value=80.0,
            status="active",
        )
        goal2 = FitnessGoal(
            member_id=m2.id,
            goal_type="cardio_fitness",
            target_value=60.0,  # e.g., target resting HR
            status="active",
        )

        db.add_all([goal1, goal2])

        # --------------------------------------------------------------
        # Classes
        # --------------------------------------------------------------
        class1 = Class(
            name="Morning Strength",
            capacity=10,
            trainer_id=t1.id,
            room_id=room1.id,
            schedule_time=datetime(2025, 12, 1, 10, 0),
        )
        class2 = Class(
            name="Evening Cardio",
            capacity=12,
            trainer_id=t2.id,
            room_id=room2.id,
            schedule_time=datetime(2025, 12, 1, 18, 0),
        )
        class3 = Class(
            name="Saturday Bootcamp",
            capacity=20,
            trainer_id=t1.id,
            room_id=room1.id,
            schedule_time=datetime(2025, 12, 6, 9, 0),
        )

        db.add_all([class1, class2, class3])
        db.flush()
        print(f"Created classes: {class1.id}, {class2.id}, {class3.id}")

        # --------------------------------------------------------------
        # Class Registrations
        # --------------------------------------------------------------
        reg1 = ClassRegistration(member_id=m1.id, class_id=class1.id)
        reg2 = ClassRegistration(member_id=m2.id, class_id=class1.id)
        reg3 = ClassRegistration(member_id=m2.id, class_id=class2.id)
        db.add_all([reg1, reg2, reg3])

        # --------------------------------------------------------------
        # PT Sessions
        # --------------------------------------------------------------
        pt1 = PTSession(
            member_id=m1.id,
            trainer_id=t3.id,
            room_id=room3.id,
            start_time=datetime(2025, 12, 1, 13, 30),
            end_time=datetime(2025, 12, 1, 14, 30),
            status="scheduled",
        )
        pt2 = PTSession(
            member_id=m2.id,
            trainer_id=t3.id,
            room_id=room3.id,
            start_time=datetime(2025, 12, 2, 15, 0),
            end_time=datetime(2025, 12, 2, 16, 0),
            status="scheduled",
        )
        db.add_all([pt1, pt2])

        # --------------------------------------------------------------
        # Equipment & Issues
        # --------------------------------------------------------------
        eq1 = Equipment(
            name="Treadmill #1",
            type="cardio",
            room_id=room2.id,
            status="operational",
        )
        eq2 = Equipment(
            name="Bench Press #1",
            type="strength",
            room_id=room1.id,
            status="operational",
        )
        db.add_all([eq1, eq2])
        db.flush()

        issue1 = EquipmentIssue(
            equipment_id=eq1.id,
            description="Strange noise at high speed",
            status="open",
        )
        db.add(issue1)

                # --------------------------------------------------------------
        # Payments
        # --------------------------------------------------------------
        now = datetime.utcnow()

        pay1 = Payment(
            member_id=m1.id,
            amount=50.0,
            method="cash",
            status="completed",
            created_at=now,
        )
        pay2 = Payment(
            member_id=m1.id,
            amount=25.0,
            method="credit",
            status="completed",
            created_at=now,
        )
        pay3 = Payment(
            member_id=m2.id,
            amount=30.0,
            method="debit",
            status="pending",
            created_at=now,
        )
        db.add_all([pay1, pay2, pay3])

        print("Seed data created successfully.")


if __name__ == "__main__":
    seed_data()
    print("Done.")
