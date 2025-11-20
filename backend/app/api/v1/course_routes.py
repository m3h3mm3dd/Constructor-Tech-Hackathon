"""
Course and task management routes for Constructor Copilot.

These endpoints allow users to create and manage courses and their
associated tasks (assignments, exams, lectures).  Courses and tasks are
persisted to the database.  For simplicity, authentication and user
scoping are not enforced; all operations act on the anonymous user.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ..deps import get_db
from ...core.security import get_api_key
from ...schemas.user import User
from ...db.models import Course, Task

router = APIRouter()


class CourseCreate(BaseModel):
    name: str = Field(..., description="Course name")
    description: Optional[str] = Field(None, description="Optional course description")
    syllabus: Optional[str] = Field(
        None,
        description="Raw syllabus or course summary.  Can be parsed later into tasks.",
    )


class CourseResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    syllabus: Optional[str]

    class Config:
        orm_mode = True


class TaskCreate(BaseModel):
    title: str = Field(..., description="Task title")
    due_date: datetime = Field(..., description="Due date and time in ISO format")
    estimated_hours: Optional[int] = Field(None, description="Estimated hours to complete")
    description: Optional[str] = Field(None, description="Task description")
    type: Optional[str] = Field(None, description="Task type, e.g. assignment, exam, lecture")


class TaskResponse(BaseModel):
    id: int
    title: str
    due_date: datetime
    estimated_hours: Optional[int]
    description: Optional[str]
    type: Optional[str]

    class Config:
        orm_mode = True


@router.post("/courses", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
async def create_course(
    course_in: CourseCreate,
    db=Depends(get_db),
    api_key: str = Depends(get_api_key),
) -> CourseResponse:
    """Create a new course.

    A course groups together tasks and can store syllabus content.  In a
    full application the course would be associated with the current user.
    """
    new_course = Course(
        name=course_in.name,
        description=course_in.description,
        syllabus=course_in.syllabus,
    )
    db.add(new_course)
    await db.commit()
    await db.refresh(new_course)
    return new_course  # type: ignore[return-value]


@router.get("/courses", response_model=List[CourseResponse])
async def list_courses(
    db=Depends(get_db),
    api_key: str = Depends(get_api_key),
) -> List[CourseResponse]:
    """List all courses."""
    # Use SQLAlchemy select to load ORM instances
    from sqlalchemy import select
    result = await db.execute(select(Course))
    courses = result.scalars().all()
    return [CourseResponse.from_orm(c) for c in courses]


@router.get("/courses/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: int,
    db=Depends(get_db),
    api_key: str = Depends(get_api_key),
) -> CourseResponse:
    """Retrieve a single course by ID."""
    course = await db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return CourseResponse.from_orm(course)


@router.post(
    "/courses/{course_id}/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_task(
    course_id: int,
    task_in: TaskCreate,
    db=Depends(get_db),
    api_key: str = Depends(get_api_key),
) -> TaskResponse:
    """Create a new task within a course."""
    course = await db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    new_task = Task(
        course_id=course.id,
        title=task_in.title,
        due_date=task_in.due_date,
        estimated_hours=task_in.estimated_hours,
        description=task_in.description,
        type=task_in.type,
    )
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    return TaskResponse.from_orm(new_task)


@router.get("/courses/{course_id}/tasks", response_model=List[TaskResponse])
async def list_tasks(
    course_id: int,
    db=Depends(get_db),
    api_key: str = Depends(get_api_key),
) -> List[TaskResponse]:
    """List tasks for a course ordered by due date."""
    course = await db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    tasks = course.tasks  # relationship; sorted by due_date
    return [TaskResponse.from_orm(t) for t in tasks]