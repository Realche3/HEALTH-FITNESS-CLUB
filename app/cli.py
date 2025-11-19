"""
Terminal CLI Application
------------------------
Simplified text-based interface to interact with the Health & Fitness Club
Management System.

Roles and Features (exposed in CLI):

Member:
    - Register and login (by email)
    - View dashboard (latest stats, goals, sessions, classes)
    - Log health metrics (historical)
    - Create fitness goals
    - Register for group classes
    - Schedule PT sessions

Trainer:
    - Login by trainer ID
    - View upcoming schedule (classes + PT sessions)
    - Define availability (non-overlapping windows)
    - Lookup assigned members (read-only goals + latest metric)

Admin:
    - Login with hardcoded credentials (demo)
    - Create trainers
    - Create rooms
    - Create classes
    - List classes for a specific day
    - Log equipment issues
    - Create and list member payments

Note:
    This CLI shows a subset of functionality to keep interaction simple
    while still demonstrating all required features for the COMP3005 project.
"""

from datetime import datetime, date
from typing import Optional

from app.db_utils import get_session

# Member services
from app.services.member_service import (
    register_member,
    update_member,
    log_health_metric,
    create_fitness_goal,
    register_for_class,
    get_member_dashboard,
)

# Trainer services
from app.services.trainer_service import (
    get_trainer,
    set_availability,
    list_availability,
    get_trainer_schedule,
    member_lookup_for_trainer,
    schedule_pt_session,
)

# Admin services
from app.services.admin_service import (
    create_room,
    list_rooms,
    create_class,
    list_classes_for_day,
    create_equipment,
    log_equipment_issue,
    create_member_payment,
    list_member_payments,
)
from models.member import Member
from models.trainer import Trainer


# --------------------------------------------------------------------------
# HELPER INPUT FUNCTIONS
# --------------------------------------------------------------------------


def prompt_int(prompt: str) -> int:
    """Prompt user for an integer, repeating until valid."""
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("Invalid integer. Please try again.")


def prompt_float(prompt: str) -> float:
    """Prompt user for a float, repeating until valid."""
    while True:
        try:
            return float(input(prompt))
        except ValueError:
            print("Invalid number. Please try again.")


def prompt_date(prompt: str) -> date:
    """Prompt user for a date in YYYY-MM-DD format."""
    while True:
        text = input(prompt + " (YYYY-MM-DD): ").strip()
        try:
            return datetime.strptime(text, "%Y-%m-%d").date()
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD.")


def prompt_datetime(prompt: str) -> datetime:
    """Prompt user for a datetime in YYYY-MM-DD HH:MM format."""
    while True:
        text = input(prompt + " (YYYY-MM-DD HH:MM): ").strip()
        try:
            return datetime.strptime(text, "%Y-%m-%d %H:%M")
        except ValueError:
            print("Invalid datetime format. Please use YYYY-MM-DD HH:MM.")


# --------------------------------------------------------------------------
# MEMBER LOGIN / REGISTRATION
# --------------------------------------------------------------------------


def find_member_by_email(email: str) -> Optional[Member]:
    """Look up a member by email."""
    with get_session() as db:
        return db.query(Member).filter(Member.email == email).first()


def member_register_flow() -> Optional[Member]:
    """Register a new member or log in if email already exists."""
    print("\n=== Member Registration ===")
    name = input("Full name: ").strip()
    email = input("Email: ").strip()
    phone = input("Phone (optional): ").strip() or None

    dob_str = input("Date of birth (YYYY-MM-DD, optional): ").strip()
    dob = None
    if dob_str:
        try:
            dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
        except ValueError:
            print("Invalid DOB format. Skipping DOB.")

    gender = input("Gender (optional): ").strip() or None

    existing = find_member_by_email(email)
    if existing:
        print("A member with this email already exists. Logging you in instead.")
        return existing

    member = register_member(
        name=name,
        email=email,
        dob=dob,
        gender=gender,
        phone=phone,
    )
    print(f"Registered successfully! Your member ID is {member.id}.")
    return member


def member_login_flow() -> Optional[Member]:
    """Login a member by email."""
    print("\n=== Member Login ===")
    email = input("Email: ").strip()
    member = find_member_by_email(email)
    if not member:
        print("No member found with that email.")
        return None
    print(f"Welcome back, {member.name}!")
    return member


# --------------------------------------------------------------------------
# MEMBER MENU
# --------------------------------------------------------------------------


def member_update_profile(member: Member) -> None:
    """Allow member to update basic profile fields."""
    print("\n=== Update Profile ===")
    print("Leave fields blank to keep current values.\n")

    new_name = input(f"Name [{member.name}]: ").strip() or None
    new_email = input("Email (optional): ").strip() or None
    new_phone = input("Phone (optional): ").strip() or None
    new_gender = input("Gender (optional): ").strip() or None

    updates = {}
    if new_name:
        updates["name"] = new_name
    if new_email:
        updates["email"] = new_email
    if new_phone:
        updates["phone"] = new_phone
    if new_gender:
        updates["gender"] = new_gender

    if not updates:
        print("No changes made.")
        return

    updated = update_member(member.id, **updates)
    if updated:
        print("Profile updated.")
        member.name = updated.name
        member.email = updated.email
        member.phone = updated.phone
        member.gender = updated.gender
    else:
        print("Failed to update profile.")


def member_menu(member: Member) -> None:
    """Display and handle member menu."""
    while True:
        print(f"\n=== Member Menu ({member.name}) ===")
        print("1. View dashboard")
        print("2. Update profile")
        print("3. Log health metric")
        print("4. Create fitness goal")
        print("5. Register for group class")
        print("6. Schedule PT session")
        print("0. Logout")

        choice = input("Select an option: ").strip()

        if choice == "1":
            dashboard = get_member_dashboard(member.id)
            print("\n--- Member Dashboard ---")
            if not dashboard:
                print("Dashboard not available.")
            else:
                for key, value in dashboard.items():
                    print(f"{key}: {value}")

        elif choice == "2":
            member_update_profile(member)

        elif choice == "3":
            print("\n=== Log Health Metric ===")
            weight = input("Weight (kg, blank to skip): ").strip()
            heart_rate = input("Heart rate (bpm, blank to skip): ").strip()
            weight_val = float(weight) if weight else None
            hr_val = int(heart_rate) if heart_rate else None
            metric = log_health_metric(member.id, weight_val, hr_val)
            print(f"Logged health metric id={metric.id} at {metric.timestamp}.")

        elif choice == "4":
            print("\n=== Create Fitness Goal ===")
            goal_type = input("Goal type (e.g., 'weight_loss'): ").strip()
            target_value = prompt_float("Target value: ")
            goal = create_fitness_goal(
                member_id=member.id,
                goal_type=goal_type,
                target_value=target_value,
                status="active",
            )
            print(f"Created goal id={goal.id}.")

        elif choice == "5":
            print("\n=== Register for Group Class ===")
            class_id = prompt_int("Class ID: ")
            success = register_for_class(member.id, class_id)
            if success:
                print("Registration successful.")
            else:
                print("Failed to register. Class may be full, invalid, or already registered.")

        elif choice == "6":
            print("\n=== Schedule PT Session ===")
            trainer_id = prompt_int("Trainer ID: ")
            room_id_str = input("Room ID (blank for none): ").strip()
            room_id = int(room_id_str) if room_id_str else None
            start_time = prompt_datetime("Session start time")
            # end_time optional, default 1 hour in service
            session = schedule_pt_session(
                member_id=member.id,
                trainer_id=trainer_id,
                room_id=room_id,
                start_time=start_time,
                end_time=None,
            )
            if session is None:
                print("Could not schedule session due to a conflict or invalid data.")
            else:
                print(f"Scheduled PT session id={session.id} at {session.start_time}.")

        elif choice == "0":
            print("Logging out...")
            break
        else:
            print("Invalid choice. Please try again.")


# --------------------------------------------------------------------------
# TRAINER LOGIN & MENU
# --------------------------------------------------------------------------


def trainer_login() -> Optional[Trainer]:
    """Simple trainer login by ID."""
    print("\n=== Trainer Login ===")
    trainer_id = prompt_int("Trainer ID: ")
    trainer = get_trainer(trainer_id)
    if not trainer:
        print("No trainer found with that ID.")
        return None
    print(f"Welcome, {trainer.name}.")
    return trainer


def trainer_menu(trainer: Trainer) -> None:
    """Display and handle trainer menu."""
    while True:
        print(f"\n=== Trainer Menu ({trainer.name}) ===")
        print("1. View upcoming schedule")
        print("2. Add availability")
        print("3. List availability")
        print("4. Lookup assigned members")
        print("0. Logout")

        choice = input("Select an option: ").strip()

        if choice == "1":
            now = datetime.now()
            print("\n=== Trainer Schedule (Upcoming) ===")
            schedule = get_trainer_schedule(trainer.id, start=now, end=None)
            print("\n-- Classes --")
            for c in schedule["classes"]:
                print(
                    f"Class ID={c.id} | {c.name} at {c.schedule_time} "
                    f"(room_id={c.room_id})"
                )
            print("\n-- PT Sessions --")
            for s in schedule["pt_sessions"]:
                print(
                    f"Session ID={s.id} | member_id={s.member_id} "
                    f"at {s.start_time} status={s.status}"
                )

        elif choice == "2":
            print("\n=== Add Availability ===")
            start = prompt_datetime("Availability start")
            end = prompt_datetime("Availability end")
            availability = set_availability(trainer.id, start, end)
            if availability is None:
                print("Failed to add availability (overlap or invalid data).")
            else:
                print(
                    f"Added availability id={availability.id} "
                    f"{availability.start_time} - {availability.end_time}"
                )

        elif choice == "3":
            print("\n=== List Availability ===")
            slots = list_availability(trainer.id)
            if not slots:
                print("No availability slots defined.")
            else:
                for a in slots:
                    print(f"ID={a.id} | {a.start_time} - {a.end_time}")

        elif choice == "4":
            print("\n=== Member Lookup (Assigned Only) ===")
            q = input("Search member name (case-insensitive): ").strip()
            results = member_lookup_for_trainer(trainer.id, q)
            if not results:
                print("No matching members found.")
            else:
                for m in results:
                    print(f"Member ID={m['member_id']} | {m['name']} ({m['email']})")
                    print(f"  Latest metric: {m['latest_metric']}")
                    print(f"  Active goals: {m['active_goals']}")

        elif choice == "0":
            print("Trainer logging out...")
            break
        else:
            print("Invalid choice. Please try again.")


# --------------------------------------------------------------------------
# ADMIN LOGIN & MENU
# --------------------------------------------------------------------------

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"  # demo only


def admin_login() -> bool:
    """Simple admin login using hardcoded credentials."""
    print("\n=== Admin Login ===")
    username = input("Username: ").strip()
    password = input("Password: ").strip()

    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        print("Admin login successful.")
        return True

    print("Invalid admin credentials.")
    return False


def admin_create_trainer() -> None:
    """Create a trainer (admin-only)."""
    print("\n=== Create Trainer ===")
    name = input("Trainer name: ").strip()
    specialization = input("Specialization (optional): ").strip() or None
    with get_session() as db:
        trainer = Trainer(name=name, specialization=specialization)
        db.add(trainer)
        db.flush()
        print(f"Created trainer id={trainer.id} name={trainer.name}.")


def admin_menu() -> None:
    """Display and handle admin menu."""
    while True:
        print("\n=== Admin Menu ===")
        print("1. Create trainer")
        print("2. Create room")
        print("3. List rooms")
        print("4. Create class")
        print("5. List classes for a day")
        print("6. Log equipment issue")
        print("7. Create member payment and list payments")
        print("0. Logout")

        choice = input("Select an option: ").strip()

        if choice == "1":
            admin_create_trainer()

        elif choice == "2":
            print("\n=== Create Room ===")
            name = input("Room name: ").strip()
            capacity = prompt_int("Room capacity: ")
            room = create_room(name=name, capacity=capacity)
            print(f"Created room id={room.id} name={room.name} capacity={room.capacity}.")

        elif choice == "3":
            rooms = list_rooms()
            print("\n--- Rooms ---")
            if not rooms:
                print("No rooms found.")
            else:
                for room in rooms:
                    print(f"ID={room.id} | {room.name} (capacity={room.capacity})")

        elif choice == "4":
            print("\n=== Create Class ===")
            name = input("Class name: ").strip()
            capacity = prompt_int("Class capacity: ")
            trainer_id = prompt_int("Trainer ID: ")
            room_id = prompt_int("Room ID: ")
            schedule_time = prompt_datetime("Class time")
            gym_class = create_class(
                name=name,
                capacity=capacity,
                trainer_id=trainer_id,
                room_id=room_id,
                schedule_time=schedule_time,
            )
            if gym_class is None:
                print("Failed to create class (check trainer/room/capacity or conflicts).")
            else:
                print(f"Created class id={gym_class.id} at {gym_class.schedule_time}.")

        elif choice == "5":
            day = prompt_date("Enter day to list classes")
            classes = list_classes_for_day(day)
            print(f"\n--- Classes on {day} ---")
            if not classes:
                print("No classes scheduled on this day.")
            else:
                for c in classes:
                    print(
                        f"ID={c.id} | {c.name} at {c.schedule_time} "
                        f"(trainer_id={c.trainer_id}, room_id={c.room_id})"
                    )

        elif choice == "6":
            print("\n=== Log Equipment Issue ===")
            eq_name = input("Equipment name: ").strip()
            room_id_str = input("Room ID (blank if not assigned): ").strip()
            room_id = int(room_id_str) if room_id_str else None
            equipment = create_equipment(
                name=eq_name,
                equipment_type=None,
                room_id=room_id,
            )
            description = input("Issue description: ").strip()
            issue = log_equipment_issue(equipment.id, description)
            if issue:
                print(f"Logged issue id={issue.id} for equipment {equipment.id}.")
            else:
                print("Failed to log issue.")

        elif choice == "7":
            print("\n=== Member Payment ===")
            member_id = prompt_int("Member ID: ")
            amount = prompt_float("Amount: ")
            method = input("Method (cash/credit/debit): ").strip()
            payment = create_member_payment(
                member_id=member_id,
                amount=amount,
                method=method,
                status="completed",
            )
            if payment:
                print(
                    f"Created payment id={payment.id} amount={payment.amount} "
                    f"status={payment.status}"
                )
                payments = list_member_payments(member_id)
                print("\n-- Member Payments --")
                for p in payments:
                    print(
                        f"ID={p.id} | amount={p.amount} status={p.status} "
                        f"method={p.method} at {p.created_at}"
                    )
            else:
                print("Failed to create payment (invalid member?).")

        elif choice == "0":
            print("Admin logging out...")
            break
        else:
            print("Invalid choice. Please try again.")


# --------------------------------------------------------------------------
# MAIN MENU
# --------------------------------------------------------------------------


def main_menu() -> None:
    """Entry point for the CLI."""
    while True:
        print("\n==============================")
        print("  Health & Fitness Club CLI  ")
        print("==============================")
        print("1. Member login")
        print("2. Member register")
        print("3. Trainer login")
        print("4. Admin login")
        print("0. Exit")

        choice = input("Select an option: ").strip()

        if choice == "1":
            member = member_login_flow()
            if member:
                member_menu(member)

        elif choice == "2":
            member = member_register_flow()
            if member:
                member_menu(member)

        elif choice == "3":
            trainer = trainer_login()
            if trainer:
                trainer_menu(trainer)

        elif choice == "4":
            if admin_login():
                admin_menu()

        elif choice == "0":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main_menu()
