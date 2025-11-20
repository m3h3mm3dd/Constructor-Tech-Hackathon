"""
Assistant routes exposing higher‑level automation features.

These endpoints provide additional functionality on top of the basic chat
interface.  They demonstrate how the underlying language model can be used
to perform common academic tasks such as study planning, FAQ summarisation
and quiz generation.  All endpoints are protected by the same API key
mechanism as the core chat routes.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ...core.security import get_api_key
from ...core.openai_client import generate
from ...llm.agent_registry import get_default_agent, AGENTS

router = APIRouter()


class Task(BaseModel):
    """A simple representation of a study or coursework task."""

    title: str = Field(..., description="Short title of the task")
    due_date: date = Field(..., description="Due date in ISO format (YYYY‑MM‑DD)")
    estimated_hours: Optional[float] = Field(
        1.0,
        description="Estimated hours required to complete the task."
    )


class PlanRequest(BaseModel):
    """Request payload for generating a daily study plan."""

    tasks: List[Task] = Field(
        ..., description="List of tasks to schedule in the plan"
    )
    plan_date: Optional[date] = Field(
        None,
        description=(
            "Date for which to generate the plan. Defaults to today if omitted."
        ),
    )
    agent: Optional[str] = Field(
        None,
        description=(
            "Name of the agent persona to use for the response (e.g. 'student' or 'prof')."
        ),
    )


class PlanResponse(BaseModel):
    """Response payload containing the generated study plan."""

    plan: str


class FAQRequest(BaseModel):
    """Request payload for summarising frequently asked questions."""

    questions: List[str] = Field(
        ..., description="List of student questions or queries"
    )
    agent: Optional[str] = Field(
        None,
        description="Name of the agent persona to answer as (defaults to base)",
    )


class FAQResponse(BaseModel):
    """Response payload containing the summarised FAQ with suggested answers."""

    summary: str


class QuizRequest(BaseModel):
    """Request payload for quiz generation."""

    text: str = Field(..., description="Source text to generate quiz questions from")
    num_questions: int = Field(
        3,
        ge=1,
        le=10,
        description="Number of quiz questions to generate (1–10)",
    )
    agent: Optional[str] = Field(
        None,
        description="Name of the agent persona to use when phrasing questions",
    )


class QuizResponse(BaseModel):
    """Response payload containing the generated quiz questions."""

    quiz: str


def _select_agent(agent_name: Optional[str]):
    """Return the agent configuration by name or default agent if None."""
    if agent_name:
        agent = AGENTS.get(agent_name)
        if not agent:
            raise HTTPException(status_code=400, detail=f"Unknown agent '{agent_name}'")
        return agent
    return get_default_agent()


@router.post("/daily-plan", response_model=PlanResponse)
async def create_daily_plan(
    request: PlanRequest,
    api_key: str = Depends(get_api_key),
) -> PlanResponse:
    """Generate a personalised daily study plan based on upcoming tasks.

    The model analyses the tasks provided, taking into account due dates
    and estimated effort, and produces a suggested schedule for the
    specified date.  Tasks with nearer deadlines and higher effort are
    prioritised.  The plan is phrased in a friendly tone suitable for
    the chosen agent persona.
    """
    # Determine the plan date: default to today if not provided
    target_date = request.plan_date or date.today()
    # Sort tasks by due date then estimated hours
    tasks_sorted = sorted(
        request.tasks,
        key=lambda t: (t.due_date, -t.estimated_hours if t.estimated_hours else 0),
    )
    # Build a concise description of tasks for the prompt
    task_lines = [
        f"- {t.title} (due {t.due_date.isoformat()}, ~{t.estimated_hours}h)"
        for t in tasks_sorted
    ]
    tasks_desc = "\n".join(task_lines)
    # Select agent (determine persona/prompt file)
    agent = _select_agent(request.agent)
    # Compose messages: system prompt from agent + user request
    # Read the system prompt file
    system_prompt_text = ""
    try:
        prompt_path = (
            __import__("importlib.resources", fromlist=["read_text"]).read_text
        )
        from app.llm import prompts as _prompts
        system_prompt_text = prompt_path(_prompts, agent.prompt_file)
    except Exception:
        system_prompt_text = "You are a helpful study planning assistant."
    messages = [
        {"role": "system", "content": system_prompt_text},
        {
            "role": "user",
            "content": (
                f"Today is {target_date.isoformat()}. Given the following list of tasks, "
                f"create a detailed study plan for the day that balances effort and prioritises "
                f"tasks with nearer deadlines. Include suggested time allocations and breaks.\n\n"
                f"Tasks:\n{tasks_desc}"
            ),
        },
    ]
    # Call the language model
    plan_text = await generate(messages, model=agent.model)
    return PlanResponse(plan=plan_text)


@router.post("/faq-summary", response_model=FAQResponse)
async def summarise_faq(
    request: FAQRequest,
    api_key: str = Depends(get_api_key),
) -> FAQResponse:
    """Summarise a list of questions into themes and provide suggested answers.

    This endpoint is useful for professors who receive many similar
    questions from students.  The assistant clusters related questions,
    identifies common themes and drafts concise, helpful answers.
    """
    if not request.questions:
        raise HTTPException(status_code=400, detail="At least one question is required")
    agent = _select_agent(request.agent)
    # Build prompt
    questions_desc = "\n".join([f"- {q}" for q in request.questions])
    system_prompt_text = ""
    try:
        prompt_path = (
            __import__("importlib.resources", fromlist=["read_text"]).read_text
        )
        from app.llm import prompts as _prompts
        system_prompt_text = prompt_path(_prompts, agent.prompt_file)
    except Exception:
        system_prompt_text = "You are a knowledgeable teaching assistant."
    messages = [
        {"role": "system", "content": system_prompt_text},
        {
            "role": "user",
            "content": (
                "Please analyse the following list of student questions, group them into common "
                "themes, and for each theme suggest a concise answer or explanation."
                "\n\nQuestions:\n" + questions_desc
            ),
        },
    ]
    summary_text = await generate(messages, model=agent.model)
    return FAQResponse(summary=summary_text)


@router.post("/generate-quiz", response_model=QuizResponse)
async def generate_quiz(
    request: QuizRequest,
    api_key: str = Depends(get_api_key),
) -> QuizResponse:
    """Generate quiz questions from a given passage of text.

    The assistant generates multiple choice questions and answers based on
    the provided text.  This can help professors quickly assemble
    formative assessments.
    """
    agent = _select_agent(request.agent)
    system_prompt_text = ""
    try:
        prompt_path = (
            __import__("importlib.resources", fromlist=["read_text"]).read_text
        )
        from app.llm import prompts as _prompts
        system_prompt_text = prompt_path(_prompts, agent.prompt_file)
    except Exception:
        system_prompt_text = "You are an expert teacher who writes clear, challenging quiz questions."
    messages = [
        {"role": "system", "content": system_prompt_text},
        {
            "role": "user",
            "content": (
                f"Create {request.num_questions} multiple choice quiz questions (with answers) "
                f"from the following material. Each question should test understanding, not "
                f"just recall. Do not repeat information verbatim from the text.\n\n"
                f"Material:\n{request.text}"
            ),
        },
    ]
    quiz_text = await generate(messages, model=agent.model)
    return QuizResponse(quiz=quiz_text)