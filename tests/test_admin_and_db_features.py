"""
Tests for admin-related operations and advanced database features:
equipment maintenance, payments, view, and stored function.
"""

from datetime import datetime

from sqlalchemy import text

from app.services.admin_service import (
    create_room,
    create_equipment,
    list_equipment,
    log_equipment_issue,
    update_equipment_issue_status,
    list_equipment_issues,
    create_member_payment,
    update_payment_status,
    list_member_payments,
)
from app.services.member_service import register_member
from app.db_utils import get_session


def test_equipment_and_issues(db_session):
    """
    Test equipment creation, logging issues, updating status, and listing.
    """
    room = create_room(name="Equip Room", capacity=3)

    equipment = create_equipment(
        name="Treadmill #1",
        equipment_type="treadmill",
        room_id=room.id,
    )
    assert equipment is not None

    eq_list = list_equipment(room_id=room.id)
    assert any(e.id == equipment.id for e in eq_list)

    issue = log_equipment_issue(equipment.id, "Belt slipping")
    assert issue is not None
    assert issue.status == "open"

    # Move issue to resolved
    updated = update_equipment_issue_status(issue.id, "resolved")
    assert updated.status == "resolved"
    assert updated.resolved_at is not None

    # List issues by room and status
    issues = list_equipment_issues(room_id=room.id, status="resolved")
    assert any(i.id == issue.id for i in issues)


def test_payments_and_view_and_function(db_session):
    """
    Test member payments, the payments view, and stored function.
    """
    email = f"payment_{int(datetime.now().timestamp())}@example.com"
    member = register_member(
        name="Payment Member",
        email=email,
        dob=None,
        gender=None,
        phone=None,
    )

    p1 = create_member_payment(
        member_id=member.id,
        amount=50.0,
        method="cash",
        status="completed",
    )
    p2 = create_member_payment(
        member_id=member.id,
        amount=25.0,
        method="credit",
        status="completed",
    )
    assert p1 is not None and p2 is not None

    # Update one payment status just to exercise the function
    updated = update_payment_status(p2.id, "completed")
    assert updated.status == "completed"

    # Check member payments list
    payments = list_member_payments(member.id)
    assert len(payments) >= 2

    # Use the view and stored function directly
    with get_session() as db:
        # View: member_payments_view
        rows = db.execute(
            text(
                "SELECT total_paid FROM member_payments_view "
                "WHERE member_id = :mid"
            ),
            {"mid": member.id},
        ).fetchall()
        assert rows
        total_from_view = rows[0][0]

        # Stored function: get_member_total_payments
        total_from_func = db.execute(
            text("SELECT get_member_total_payments(:mid)"),
            {"mid": member.id},
        ).scalar()

        # Both should match the sum of amounts (50 + 25)
        assert float(total_from_view) == float(total_from_func) == 75.0
