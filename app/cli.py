"""
Terminal CLI Application
------------------------
Simple text-based interface to interact with the Health & Fitness Club
Management System.

Features:
    - Member registration and login (by email).
    - Member actions:
        * View profile
        * Log health metrics
        * Create fitness goals
        * Record payments
    - Admin login (hardcoded credentials).
    - Admin actions:
        * Create rooms
        * List rooms
        * Create classes
        * List classes for a given day

Note:
    This CLI is intended for demonstration purposes for the COMP3005 project.
    Authentication is basic (no passwords for members, admin password hardcoded).
"""

from datetime import datetime, date
from typing import Optional



from app.db_utils import get_session
from app.services.member_service import (
    register_member,
    log_health_metric,
    create_fitness_goal,
    record_payment,
    get_member_profile,
)
from app.services.admin_service import (
    create_room,
    list_rooms,
    create_class,
    list_classes_for_day,
)
from models.member import Member
from models.pt_session import PTSession  # noqa: F401  # imported for relationship resolution


# --------------------------------------------------------------------------
# HELPER INPUT FUNCTIONS
# --------------------------------------------------------------------------

def prompt_int(prompt: str) -> int:
    """
    Prompt the user for an integer input, repeating until a valid integer is given.

    Args:
        prompt (str): Text to display to the user.

    Returns:
        int: Parsed integer value.
    """
    while True:
        try:
            value = int(input(prompt))
            return value
        except ValueError:
            print("Invalid integer. Please try again.")


def prompt_float(prompt: str) -> float:
    """
    Prompt the user for a float input, repeating until a valid float is given.

    Args:
        prompt (str): Text to display to the user.

    Returns:
        float: Parsed float value.
    """
    while True:
        try:
            value = float(input(prompt))
            return value
        except ValueError:
            print("Invalid number. Please try again.")


def prompt_date(prompt: str) -> date:
    """
    Prompt the user for a date in YYYY-MM-DD format.

    Args:
        prompt (str): Text to display.

    Returns:
        date: Parsed date object.
    """
    while True:
        text = input(prompt + " (YYYY-MM-DD): ")
        try:
            return datetime.strptime(text, "%Y-%m-%d").date()
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD.")


def prompt_datetime(prompt: str) -> datetime:
    """
    Prompt the user for a datetime in YYYY-MM-DD HH:MM format.

    Args:
        prompt (str): Text to display.

    Returns:
        datetime: Parsed datetime object.
    """
    while True:
        text = input(prompt + " (YYYY-MM-DD HH:MM): ")
        try:
            return datetime.strptime(text, "%Y-%m-%d %H:%M")
        except ValueError:
            print("Invalid datetime format. Please use YYYY-MM-DD HH:MM.")


# --------------------------------------------------------------------------
# MEMBER LOGIN / REGISTRATION
# --------------------------------------------------------------------------

def find_member_by_email(email: str) -> Optional[Member]:
    """
    Look up a member by email using ORM.

    Args:
        email (str): Member email to search for.

    Returns:
        Member | None: Matching Member or None if not found.
    """
    with get_session() as db:
        return db.query(Member).filter(Member.email == email).first()


def member_register_flow() -> Optional[Member]:
    """
    Handle member registration interaction via the terminal.

    Returns:
        Member | None: Newly created Member object or None if failed.
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
    """
    Handle member login by email.

    Returns:
        Member | None: Logged in member or None if not found.
    """
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

def member_menu(member: Member) -> None:
    """
    Display and handle the member menu for a logged-in member.

    Args:
        member (Member): Currently logged-in member.
    """
    while True:
        print(f"\n=== Member Menu ({member.name}) ===")
        print("1. View profile summary")
        print("2. Log health metric")
        print("3. Create fitness goal")
        print("4. Record payment")
        print("0. Logout")

        choice = input("Select an option: ").strip()

        if choice == "1":
            profile = get_member_profile(member.id)
            print("\n--- Profile Summary ---")
            if profile:
                for key, value in profile.items():
                    print(f"{key}: {value}")
            else:
                print("Profile not found.")

        elif choice == "2":
            weight = input("Weight (kg, blank to skip): ").strip()
            heart_rate = input("Heart rate (bpm, blank to skip): ").strip()

            weight_val = float(weight) if weight else None
            hr_val = int(heart_rate) if heart_rate else None

            metric = log_health_metric(
                member_id=member.id,
                weight=weight_val,
                heart_rate=hr_val,
            )
            print(f"Logged health metric with id={metric.id} at {metric.timestamp}.")

        elif choice == "3":
            goal_type = input("Goal type (e.g., 'weight loss'): ").strip()
            target_value = prompt_float("Target value: ")
            goal = create_fitness_goal(
                member_id=member.id,
                goal_type=goal_type,
                target_value=target_value,
                status="active",
            )
            print(f"Created goal id={goal.id} for member {member.name}.")

        elif choice == "4":
            amount = prompt_float("Payment amount: ")
            method = input("Payment method (e.g., credit, debit, cash): ").strip()
            payment = record_payment(
                member_id=member.id,
                amount=amount,
                method=method,
                status="completed",
            )
            print(f"Recorded payment id={payment.id} at {payment.created_at}.")

        elif choice == "0":
            print("Logging out...")
            break
        else:
            print("Invalid choice. Please try again.")


# --------------------------------------------------------------------------
# ADMIN LOGIN & MENU
# --------------------------------------------------------------------------

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"  # For demo only


def admin_login() -> bool:
    """
    Simple admin login using hardcoded credentials.

    Returns:
        bool: True if login successful, False otherwise.
    """
    print("\n=== Admin Login ===")
    username = input("Username: ").strip()
    password = input("Password: ").strip()

    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        print("Admin login successful.")
        return True

    print("Invalid admin credentials.")
    return False


def admin_menu() -> None:
    """
    Display and handle the admin menu, assuming the admin is already logged in.
    """
    while True:
        print("\n=== Admin Menu ===")
        print("1. Create room")
        print("2. List rooms")
        print("3. Create class")
        print("4. List classes for a day")
        print("0. Logout")

        choice = input("Select an option: ").strip()

        if choice == "1":
            name = input("Room name: ").strip()
            capacity = prompt_int("Room capacity: ")
            room = create_room(name=name, capacity=capacity)
            print(f"Created room id={room.id} name={room.name} capacity={room.capacity}.")

        elif choice == "2":
            rooms = list_rooms()
            print("\n--- Rooms ---")
            if not rooms:
                print("No rooms found.")
            else:
                for room in rooms:
                    print(f"ID={room.id} | {room.name} (capacity={room.capacity})")

        elif choice == "3":
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
                print("Failed to create class. Check trainer/room IDs and capacity.")
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
    Entry point for the CLI. Displays the main menu and routes the user
    to member or admin flows.
    """
    while True:
        print("\n==============================")
        print("  Health & Fitness Club CLI  ")
        print("==============================")
        print("1. Member login")
        print("2. Member register")
        print("3. Admin login")
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
            if admin_login():
                admin_menu()

        elif choice == "0":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main_menu()
