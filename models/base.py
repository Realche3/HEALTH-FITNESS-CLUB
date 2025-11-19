"""
Base ORM Declaration
--------------------
This file defines the SQLAlchemy Declarative Base used by all ORM models
in the project. Every model must inherit from this Base class.
"""

from sqlalchemy.orm import declarative_base

Base = declarative_base()
