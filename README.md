# Health & Fitness Club Management System
COMP3005 Final Project  
Student: Mohamed Cherif Bah — ID: 101292844  
Course: Group Final Project 79

---

## Overview

This project implements a complete Health & Fitness Club Management System using:

- Python 3 (SQLAlchemy ORM)
- PostgreSQL
- Alembic for database migrations
- A guided Command-Line Interface (CLI v3)

The system supports three user roles and enforces all necessary business rules:

- Members  
- Trainers  
- Administrative staff

The database layer includes a SQL View, Trigger, Stored Function, and Index, meeting all COMP3005 requirements.

---

## Features

### Member Features
- Register and log in by email
- View personal dashboard (latest metrics, goals, classes, PT sessions)
- Update profile
- Log health metrics with timestamps
- Create fitness goals
- Register for group classes (capacity + conflict checks)
- Schedule personal training sessions (conflict-free scheduling)

### Trainer Features
- Log in from trainer list
- Add availability (overlap prevention)
- View upcoming schedule (classes + PT sessions)
- Lookup assigned members (read-only)

### Admin Features
- Log in with demo credentials
- Create trainers
- Create rooms
- Schedule classes (trainer + room selection)
- View classes for a selected day
- Record member payments

---

## Advanced Database Features

| Feature | Description |
|--------|-------------|
| SQL View | `member_payments_view` — aggregated member payments |
| Stored Function | `get_member_total_payments(member_id)` |
| Trigger | Auto-completes weight-loss goals when target is reached |
| Index | Index on `members.email` for fast lookup |

---

## Project Structure

```
HEALTH-FITNESS-CLUB/
├── app/
│   ├── cli.py                # CLI v3
│   ├── seed_data.py          # Test data generator
│   ├── clear_data.py         # Remove all table rows
│   ├── db.py                 # SQLAlchemy engine + session
│   ├── db_utils.py           # get_session() context manager
│   ├── services/
│   │   ├── member_service.py
│   │   ├── trainer_service.py
│   │   └── admin_service.py
│   └── api/                  # (Optional FastAPI routers)
│
├── models/                   # ORM entity definitions
├── alembic/                  # Migrations
├── tests/                    # pytest suite
├── docs/
│   ├── report.pdf
│   ├── ERD.png
│   └── demo.mp4
└── README.md
```

---

## Running the Project

### 1. Install dependencies
```
pip install -r requirements.txt
```

### 2. Configure database
Edit the PostgreSQL connection URL in `app/db.py`.

### 3. Apply migrations
```
alembic upgrade head
```

### 4. (Optional) Seed demo data
```
python -m app.seed_data
```

### 5. Launch the CLI
```
python -m app.cli
```

---

## Running Tests

The project includes pytest-based tests. Run them with:

```
pytest
```

The tests cover:

- Member workflows
- Trainer workflows
- Admin workflows
- Scheduling conflicts
- Capacity rules
- Trigger, view, and stored function validation

---

## Documentation

All documentation is in the `docs/` folder:

- report.pdf — Final project report  
- ERD.png — Entity Relationship Diagram  
- demo.mp4 — CLI demonstration video  

---

## Requirements Checklist

| Requirement | Status |
|------------|--------|
| Minimum 6 tables | Completed |
| Minimum 8 advanced operations | Completed |
| SQL View | Completed |
| Stored Function | Completed |
| Trigger | Completed |
| Index | Completed |
| ORM usage (no raw SQL except required objects) | Completed |
| Full working system | Completed |
| ERD + Report + Video Demo | Completed |

---

## Author
Mohamed Cherif Bah  
Carleton University  
COMP3005 Final Project
