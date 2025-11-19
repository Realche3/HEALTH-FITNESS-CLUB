# app/db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.base import Base  # so Alembic / others can access Base here

# Database URL
DATABASE_URL = "postgresql+psycopg2://postgres:622950678@localhost:5432/fitness_club"

# Engine: main connection object
engine = create_engine(
    DATABASE_URL,
    echo=True,      # Shows SQL in console
    future=True,
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit= False,
    bind=engine,
)

# Dependency for FastAPI / or just use directly in CLI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
