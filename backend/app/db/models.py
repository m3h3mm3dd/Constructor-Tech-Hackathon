"""
ORM model definitions using SQLAlchemy.

Defines ``User``, ``ChatSession``, and ``Message`` tables. These models
are simplistic and can be extended with additional fields or relations.
"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .base import Base


class User(Base):
    """User account model."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

    messages = relationship("Message", back_populates="user", cascade="all, delete-orphan")


class ChatSession(Base):
    """Chat session model representing a conversation between a user and the agent."""

    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="sessions")
    messages = relationship(
        "Message",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="Message.id",
    )


class Message(Base):
    """Individual chat message within a session."""

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("ChatSession", back_populates="messages")
    user = relationship("User", back_populates="messages")


# ---------------------------------------------------------------------------
# Extended domain models for Constructor Copilot

class Course(Base):
    """Course model representing a university course.

    Each course belongs to a user (instructor or student) and may have
    associated tasks such as assignments, exams or lectures.  A course
    can also store raw syllabus text or imported calendar data.
    """

    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    syllabus = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="courses")
    tasks = relationship(
        "Task",
        back_populates="course",
        cascade="all, delete-orphan",
        order_by="Task.due_date",
    )


class Task(Base):
    """Task model representing an assignment, exam or lecture event.

    Tasks belong to courses and include metadata such as due date,
    estimated hours and description.  They are used to generate study
    plans and reminders.
    """

    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(DateTime, nullable=False)
    estimated_hours = Column(Integer, nullable=True)
    type = Column(String, nullable=True)  # e.g. 'assignment', 'exam', 'lecture'
    created_at = Column(DateTime, default=datetime.utcnow)

    course = relationship("Course", back_populates="tasks")