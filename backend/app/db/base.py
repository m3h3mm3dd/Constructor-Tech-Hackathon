"""
Declarative base for SQLAlchemy models.

All ORM models should inherit from ``Base`` defined here. Separating the
declarative base into its own module avoids circular imports when models
reference each other.
"""

from sqlalchemy.orm import declarative_base


Base = declarative_base()