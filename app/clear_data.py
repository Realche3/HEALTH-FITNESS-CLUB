"""
Clear Data Script
-----------------
Utility script to remove ALL data from the Health & Fitness Club
database tables, without dropping the schema.

This is useful for resetting the database before re-seeding
with fresh test data.

Usage:
    From the project root (virtualenv activated):

        python -m app.clear_data

Note:
    - Uses SQLAlchemy ORM delete() calls in a foreign-key-safe order:
      child tables are cleared before parent tables.
    - Does NOT drop tables or alter schema.
"""

from app.db_utils import get_session

from models.equipment_issue import EquipmentIssue
from models.class_registration import ClassRegistration
from models.pt_session import PTSession
from models.trainer_availability import TrainerAvailability
from models.health_metric import HealthMetric
from models.fitness_goal import FitnessGoal
from models.payment import Payment
from models.equipment import Equipment
from models.class_ import Class
from models.room import Room
from models.trainer import Trainer
from models.member import Member


def clear_all_data() -> None:
    """
    Delete all rows from all tables in an order that respects
    foreign key constraints.
    """
    print("Clearing all data from database (rows only, schema preserved)...")

    with get_session() as db:
        # Child tables first
        db.query(EquipmentIssue).delete()
        db.query(ClassRegistration).delete()
        db.query(PTSession).delete()
        db.query(TrainerAvailability).delete()
        db.query(HealthMetric).delete()
        db.query(FitnessGoal).delete()
        db.query(Payment).delete()
        db.query(Equipment).delete()
        db.query(Class).delete()
        db.query(Room).delete()
        db.query(Trainer).delete()
        db.query(Member).delete()

        print("All data cleared.")


if __name__ == "__main__":
    clear_all_data()
    print("Done.")
