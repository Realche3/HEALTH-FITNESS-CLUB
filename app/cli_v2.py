"""
Health & Fitness Club - CLI v3
------------------------------
Clean, guided, and minimal command-line interface for the
Health & Fitness Club Management System.

Goals:
    - Easy to demo.
    - Minimal menu options.
    - Guided workflows (always list existing data before asking for IDs).
    - Only expose core flows needed to show requirements.

Roles & Flows:

Member:
    - Register / Login by email
    - View dashboard (latest metrics, goals, classes, PT sessions)
    - Log a health metric
    - Create a fitness goal
    - Book a group class (pick day → see classes → choose one)
    - Book a PT session (see trainers → choose one → choose room → time)

Trainer:
    - Login (choose from list of trainers)
    - View upcoming schedule (classes + PT sessions)
    - Add availability (no overlap)
    - Lookup assigned members (read-only goals + latest metric)

Admin:
    - Login (hardcoded demo credentials)
    - Create trainer
    - Create room
    - Schedule class (choose trainer + room)
    - View classes for a given day
    - Record member payment (choose member → enter amount/method)

Note:
    This CLI is intentionally simple. All heavy business rules live in the
    service layer and are enforced by SQLAlchemy ORM and PostgreSQL.
"""

from datetime import datetime, date
from typing import Optional, List, TypeVar, Callable

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
    create_member_payment,
    list_member_payments,
)

# ORM models used for listing/selection
from models.member import Member
from models.trainer import Trainer
from models.room import Room

# Generic type for selection helper
T = TypeVar("T")


# --------------------------------------------------------------------------
# BASIC INPUT HELPERS
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
# GENERIC SELECTION HELPER
# --------------------------------------------------------------------------


def choose_from_list(
    items: List[T],
    label: str,
    formatter: Callable[[T], str],
) -> Optional[T]:
    """
    Generic helper: print a list of items and let user pick one by ID.

    Args:
        items: List of objects to choose from.
        label: Label for the list (e.g., "Members", "Trainers").
        formatter: Function that converts each object to a display string.

    Returns:
        The chosen object, or None if list is empty or invalid choice.
    """
    print(f"\n=== {label} ===")
    if not items:
        print(f"No {label.lower()} found.")
        return None

    for item in items:
        print(formatter(item))

    try:
        chosen_id = int(input(f"Enter ID of the {label[:-1]}: ").strip())
    except ValueError:
        print("Invalid input.")
        return None

    for item in items:
        # Assume each item has an 'id' attribute
        if getattr(item, "id", None) == chosen_id:
            return item

    print(f"No {label[:-1]} with that ID.")
    return None


# --------------------------------------------------------------------------
# LIST HELPERS FOR SPECIFIC ENTITIES
# --------------------------------------------------------------------------


def list_members() -> List[Member]:
    """Fetch and print all members, return list."""
    with get_session() as db:
        members = db.query(Member).order_by(Member.id).all()

    if not members:
        print("\n=== Members ===")
        print("No members found.")
    else:
        print("\n=== Members ===")
        for m in members:
            print(f"ID={m.id} | {m.name} ({m.email})")

    return members


def choose_member() -> Optional[Member]:
    """Guided selection: choose a member from printed list."""
    with get_session() as db:
        members = db.query(Member).order_by(Member.id).all()
    return choose_from_list(members, "Members", lambda m: f"ID={m.id} | {m.name} ({m.email})")


def list_trainers() -> List[Trainer]:
    """Fetch and print all trainers, return list."""
    with get_session() as db:
        trainers = db.query(Trainer).order_by(Trainer.id).all()

    print("\n=== Trainers ===")
    if not trainers:
        print("No trainers found. Ask admin to create some.")
    else:
        for t in trainers:
            print(f"ID={t.id} | {t.name} (specialization={t.specialization})")

    return trainers


def choose_trainer() -> Optional[Trainer]:
    """Guided selection: choose a trainer from printed list."""
    with get_session() as db:
        trainers = db.query(Trainer).order_by(Trainer.id).all()
    return choose_from_list(trainers, "Trainers", lambda t: f"ID={t.id} | {t.name} ({t.specialization})")


def list_rooms_simple() -> List[Room]:
    """Fetch and print all rooms, return list."""
    rooms = list_rooms()
    print("\n=== Rooms ===")
    if not rooms:
        print("No rooms found.")
    else:
        for r in rooms:
            print(f"ID={r.id} | {r.name} (capacity={r.capacity})")
    return rooms


def choose_room() -> Optional[Room]:
    """Guided selection: choose a room from printed list."""
    rooms = list_rooms()
    return choose_from_list(rooms, "Rooms", lambda r: f"ID={r.id} | {r.name} (capacity={r.capacity})")


# --------------------------------------------------------------------------
# MEMBER LOGIN / REGISTRATION
# --------------------------------------------------------------------------


def find_member_by_email(email: str) -> Optional[Member]:
    """Look up a member by email."""
    with get_session() as db:
        return db.query(Member).filter(Member.email == email).first()


def member_register_flow() -> Optional[Member]:
    """
    Register a new member. If email already exists,
    log in that member instead.
    """
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
    """Login a member by email only (simple auth)."""
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
    """Allow member to update a few profile fields."""
    print("\n=== Update Profile ===")
    print("Leave fields blank to keep current values.\n")

    new_name = input(f"Name [{member.name}]: ").strip() or None
    new_phone = input(f"Phone [{member.phone or ''}]: ").strip() or None
    new_gender = input(f"Gender [{member.gender or ''}]: ").strip() or None

    updates = {}
    if new_name:
        updates["name"] = new_name
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
        member.phone = updated.phone
        member.gender = updated.gender
    else:
        print("Failed to update profile.")


def member_choose_class_for_day() -> Optional[int]:
    """
    Guided flow: ask for a day, list all classes that day, let member pick one.

    Returns:
        int | None: chosen class ID, or None if none selected/available.
    """
    day = prompt_date("Enter day to see available classes")
    classes = list_classes_for_day(day)
    print(f"\n--- Classes on {day} ---")
    if not classes:
        print("No classes scheduled on this day.")
        return None

    for c in classes:
        print(
            f"ID={c.id} | {c.name} at {c.schedule_time} "
            f"(trainer_id={c.trainer_id}, room_id={c.room_id})"
        )

    class_id = prompt_int("Enter the ID of the class you want to register for: ")
    return class_id


def member_menu(member: Member) -> None:
    """Main menu for a logged-in member (compact and guided)."""
    while True:
        print(f"\n=== Member Menu ({member.name}) ===")
        print("1. View dashboard")
        print("2. Update profile")
        print("3. Log health metric")
        print("4. Create fitness goal")
        print("5. Book group class")
        print("6. Book PT session")
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
            print("\n=== Book Group Class ===")
            class_id = member_choose_class_for_day()
            if class_id is None:
                print("No class selected.")
            else:
                success = register_for_class(member.id, class_id)
                if success:
                    print("Registration successful.")
                else:
                    print("Failed to register. Class may be full, invalid, or already registered.")

        elif choice == "6":
            print("\n=== Book PT Session ===")
            trainer = choose_trainer()
            if not trainer:
                print("Cannot book PT session without a trainer.")
                continue

            room = choose_room()
            room_id = room.id if room else None

            start_time = prompt_datetime("Session start time")
            session = schedule_pt_session(
                member_id=member.id,
                trainer_id=trainer.id,
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
    """
    Trainer login: show all trainers, let them pick their ID.
    Simple but more user friendly than typing ID blindly.
    """
    print("\n=== Trainer Login ===")
    trainers = list_trainers()
    if not trainers:
        return None

    trainer = choose_trainer()
    if not trainer:
        return None

    print(f"Welcome, {trainer.name}.")
    return trainer


def trainer_menu(trainer: Trainer) -> None:
    """Main menu for a logged-in trainer."""
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
    """Create a trainer (admin-only, guided)."""
    print("\n=== Create Trainer ===")
    name = input("Trainer name: ").strip()
    specialization = input("Specialization (optional): ").strip() or None
    with get_session() as db:
        trainer = Trainer(name=name, specialization=specialization)
        db.add(trainer)
        db.flush()
        print(f"Created trainer id={trainer.id} name={trainer.name}.")


def admin_menu() -> None:
    """Main menu for logged-in admin (minimal but complete)."""
    while True:
        print("\n=== Admin Menu ===")
        print("1. Create trainer")
        print("2. Create room")
        print("3. Schedule class")
        print("4. View classes for a day")
        print("5. Record member payment")
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
            print("\n=== Schedule Class ===")
            name = input("Class name: ").strip()
            capacity = prompt_int("Class capacity: ")

            trainer = choose_trainer()
            if not trainer:
                print("Cannot create class without a valid trainer.")
                continue

            room = choose_room()
            if not room:
                print("Cannot create class without a valid room.")
                continue

            schedule_time = prompt_datetime("Class time")
            gym_class = create_class(
                name=name,
                capacity=capacity,
                trainer_id=trainer.id,
                room_id=room.id,
                schedule_time=schedule_time,
            )
            if gym_class is None:
                print("Failed to create class (capacity or room conflict).")
            else:
                print(f"Created class id={gym_class.id} at {gym_class.schedule_time}.")

        elif choice == "4":
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

        elif choice == "5":
            print("\n=== Record Member Payment ===")
            member = choose_member()
            if not member:
                print("Cannot create payment without a valid member.")
                continue

            amount = prompt_float("Amount: ")
            method = input("Method (cash/credit/debit): ").strip()
            payment = create_member_payment(
                member_id=member.id,
                amount=amount,
                method=method,
                status="completed",
            )
            if payment:
                print(
                    f"Created payment id={payment.id} amount={payment.amount} "
                    f"status={payment.status}"
                )
                payments = list_member_payments(member.id)
                print("\n-- Member Payments --")
                for p in payments:
                    print(
                        f"ID={p.id} | amount={p.amount} status={p.status} "
                        f"method={p.method} at {p.created_at}"
                    )
            else:
                print("Failed to create payment.")

        elif choice == "0":
            print("Admin logging out...")
            break
        else:
            print("Invalid choice. Please try again.")


# --------------------------------------------------------------------------
# MAIN MENU
# --------------------------------------------------------------------------


def main_menu() -> None:
    """
    Entry point for the CLI.
    Users choose their role, then follow guided menus.
    """
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
