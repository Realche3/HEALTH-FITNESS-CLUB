# app/db_utils.py
from contextlib import contextmanager
from app.db import SessionLocal

@contextmanager
def get_session():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()
