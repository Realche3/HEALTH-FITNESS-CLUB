"""
Add DB View, Stored Function, and Trigger
-----------------------------------------
This migration adds the following PostgreSQL objects:

1. View: member_payments_view
   - Shows, for each member:
       * member_id
       * member_name
       * total_paid (SUM of payments.amount)
       * last_payment_date (MAX of payments.created_at)

2. Stored function: get_member_total_payments(member_id)
   - Returns the total amount paid by a given member.
   - Intended to satisfy the COMP3005 "stored function" requirement.
   - Can be called from SQL or via SQLAlchemy text() if desired.

3. Trigger function + trigger: check_weight_goal_completion
   - Trigger function:
       * When a new HealthMetric row is inserted, if the weight
         meets or beats an active 'weight_loss' goal, that goal
         is marked as 'completed'.
   - Trigger:
       * Attached to the health_metrics table, AFTER INSERT, FOR EACH ROW.

All of this is implemented with raw SQL using Alembic's op.execute(),
which is allowed for database-level objects (views, triggers, functions),
while the application logic continues to use SQLAlchemy ORM.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# Revision identifiers, used by Alembic.
revision: str = 'a2c71be37ca1'
down_revision: Union[str, Sequence[str], None] = '9a445945a1cf'

branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Apply the migration.

    This function creates:
        - member_payments_view
        - get_member_total_payments()
        - check_weight_goal_completion() (trigger function)
        - trg_check_weight_goal_completion (trigger)
    """

    # ------------------------------------------------------------------
    # 1) VIEW: member_payments_view
    # ------------------------------------------------------------------
    op.execute(
        """
        CREATE OR REPLACE VIEW member_payments_view AS
        SELECT
            m.id   AS member_id,
            m.name AS member_name,
            COALESCE(SUM(p.amount), 0) AS total_paid,
            MAX(p.created_at)          AS last_payment_date
        FROM members m
        LEFT JOIN payments p
            ON p.member_id = m.id
        GROUP BY m.id, m.name;
        """
    )

    # ------------------------------------------------------------------
    # 2) STORED FUNCTION: get_member_total_payments(member_id)
    # ------------------------------------------------------------------
    op.execute(
        """
        CREATE OR REPLACE FUNCTION get_member_total_payments(p_member_id INT)
        RETURNS NUMERIC AS
        $$
        DECLARE
            total NUMERIC;
        BEGIN
            SELECT COALESCE(SUM(amount), 0) INTO total
            FROM payments
            WHERE member_id = p_member_id;

            RETURN total;
        END;
        $$
        LANGUAGE plpgsql;
        """
    )

    # ------------------------------------------------------------------
    # 3) TRIGGER FUNCTION: check_weight_goal_completion()
    # ------------------------------------------------------------------
    op.execute(
        """
        CREATE OR REPLACE FUNCTION check_weight_goal_completion()
        RETURNS TRIGGER AS
        $$
        BEGIN
            -- If no weight was recorded, do nothing.
            IF NEW.weight IS NULL THEN
                RETURN NEW;
            END IF;

            -- Mark active 'weight_loss' goals as completed if the
            -- new weight is less than or equal to the target value.
            UPDATE fitness_goals
            SET status = 'completed'
            WHERE member_id = NEW.member_id
              AND goal_type = 'weight_loss'
              AND status = 'active'
              AND target_value IS NOT NULL
              AND NEW.weight <= target_value;

            RETURN NEW;
        END;
        $$
        LANGUAGE plpgsql;
        """
    )

    # ------------------------------------------------------------------
    # 4) TRIGGER: trg_check_weight_goal_completion ON health_metrics
    # ------------------------------------------------------------------
    op.execute(
        """
        CREATE TRIGGER trg_check_weight_goal_completion
        AFTER INSERT ON health_metrics
        FOR EACH ROW
        EXECUTE FUNCTION check_weight_goal_completion();
        """
    )


def downgrade() -> None:
    """
    Revert the migration.

    This function drops:
        - trg_check_weight_goal_completion (trigger)
        - check_weight_goal_completion() (trigger function)
        - get_member_total_payments() (stored function)
        - member_payments_view
    """

    # Drop trigger first (depends on the trigger function)
    op.execute(
        """
        DROP TRIGGER IF EXISTS trg_check_weight_goal_completion
        ON health_metrics;
        """
    )

    # Drop trigger function
    op.execute(
        """
        DROP FUNCTION IF EXISTS check_weight_goal_completion();
        """
    )

    # Drop stored function
    op.execute(
        """
        DROP FUNCTION IF EXISTS get_member_total_payments(INT);
        """
    )

    # Drop view
    op.execute(
        """
        DROP VIEW IF EXISTS member_payments_view;
        """
    )
