# Constructor Copilot Backend

This repository contains the backend service for **Constructor Copilot** –
an AI‑powered campus assistant that senses your course data, thinks
about what matters, and acts on your behalf.  Constructor Copilot is
designed for students and professors at Constructor University who want
to stay on top of coursework and teach more effectively.  It goes
beyond a simple chatbot by ingesting syllabi, assignments and
questions, planning your study schedule, generating reminders, and
preparing teaching materials.

The service is built with [FastAPI](https://fastapi.tiangolo.com/) and
integrates with [OpenRouter](https://openrouter.ai/) via the OpenAI
Python SDK.  OpenRouter hosts free and paid community models behind an
OpenAI‑compatible API; Constructor Copilot defaults to the free
`openai/gpt‑oss‑20b:free` model.  The backend is organised into clear
layers – API routes, service logic, data access, LLM helpers and
database models – making it easy to extend and customise.

The default personas include a *student mode* (friendly, step‑by‑step
explanations) and a *professor mode* (formal, pedagogy‑focused).  You
can add additional personas by editing `app/llm/agent_registry.py` and
providing prompt files in `app/llm/prompts/`.

## Core Features

Constructor Copilot is built around the agent triad **sense → decide → act**.
The backend exposes endpoints and models to support each stage:

* **Multi‑persona agents:** Define multiple agents with different
  personas and prompts in `app/llm/agent_registry.py`.  The default
  agents are `base`, `student` and `prof`, all using
  `openai/gpt‑oss‑20b:free`.  Tools are disabled by default but can be
  enabled when using paid models that support function calling.

* **Sense (input layer):**
  - **Course & task management:** Endpoints under `/api/v1/courses`
    let you create courses, store raw syllabi and attach tasks such as
    assignments, exams and lectures.  Each task records a due date and
    estimated hours.
  - **Document ingestion (RAG):** The `/api/v1/rag` endpoints allow
    you to upload PDFs or plain text into an embedding store (powered
    by LangChain and Chroma).  These documents can later be retrieved
    and used to ground model responses.
  - **(Optional) Calendar import:** The codebase is structured to
    allow future integration with iCal/Google Calendar.  You can add
    endpoints to parse calendar feeds and populate tasks.

* **Decide (brain):**
  - **Personalised daily plan:** `POST /api/v1/assistant/daily-plan`
    analyses a list of tasks and due dates to produce a detailed
    schedule for a given day, balancing effort and prioritising
    imminent deadlines.
  - **FAQ summarisation:** `POST /api/v1/assistant/faq-summary` groups
    student questions into common themes and drafts concise answers.
  - **Quiz generation:** `POST /api/v1/assistant/generate-quiz` turns a
    passage of text into multiple choice questions and answers,
    helping professors create formative assessments.
  - **(Optional) Reminder scheduling:** You can extend the plan
    endpoint or add a new route to generate a schedule of reminders
    relative to each task’s due date (e.g. T‑7, T‑2).  Example code
    for this is included in comments in `assistant_routes.py`.

* **Act (automation):**
  - **Daily study digest:** The daily plan endpoint can be invoked
    automatically (e.g. by a scheduled task or button in the frontend)
    to present a morning summary of what to focus on today.
  - **Smart reminders:** By analysing tasks and deadlines the backend
    can propose a sequence of reminders.  In a production setting
    these could be scheduled via Celery and delivered via email or
    push notifications.  For the hackathon demo you can simulate the
    reminders in your UI.
  - **Office hours assistance:** The FAQ summarisation endpoint helps
    professors prepare for office hours by clustering student
    questions, highlighting the most confusing topics and drafting
    responses.

* **Additional capabilities:**
  - **Streaming chat:** Real‑time SSE responses via `/api/v1/chat/stream`.
  - **Database integration:** Uses SQLAlchemy with async sessions.
    Default uses SQLite; configuration for PostgreSQL/Redis provided.
  - **Background tasks:** Celery and Redis are integrated (but
    optional) for long‑running RAG ingestion and scheduled jobs.
  - **Extensible tools:** While disabled for the free model, you can
    implement custom tools under `app/llm/tools/` and enable them when
    using models that support function calling.

## Getting Started

1. **Install dependencies**

   It’s best to work in a fresh virtual environment.  From the
   `backend` directory run:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure environment variables**

   - `OPENAI_API_KEY` – your OpenRouter API key (starts with `sk-or-`).
   - `CORS_ORIGINS` – JSON array of allowed frontend origins (e.g. `["http://localhost:3000"]`).
   - `DB_URL` – database connection string (defaults to SQLite file `test.db`).
   - `VECTOR_DB_URL` – folder to persist document embeddings, or leave blank for in‑memory.

   For a demo you can leave the Redis/Celery settings commented out.

3. **Initialise the database**

   For SQLite the tables are created automatically on startup.  A
   helper script seeds a demo user:

   ```bash
   # optional
   python3 -m scripts.dev_seed
   ```

   If you’re using a different database, edit `alembic.ini` and run
   migrations with:

   ```bash
   alembic upgrade head
   ```

4. **Run the server**

   Start the FastAPI app:

   ```bash
   uvicorn app.main:app --reload
   ```

   The API will be available at `http://localhost:8000`.  Interactive
   Swagger docs are at `http://localhost:8000/docs`.

5. **Use the API**

   Explore endpoints via Swagger UI or use your favourite HTTP client.
   Here are some example workflows:

   **Create a course and tasks**

   ```bash
   curl -X POST http://localhost:8000/api/v1/courses \
        -H "X-API-Key: <your key>" \
        -H "Content-Type: application/json" \
        -d '{"name": "Algorithms", "description": "Intro to algorithms"}'

   # Suppose the new course has ID 1
   curl -X POST http://localhost:8000/api/v1/courses/1/tasks \
        -H "X-API-Key: <your key>" \
        -H "Content-Type: application/json" \
        -d '{"title": "Assignment 1", "due_date": "2025-11-30T23:59:00", "estimated_hours": 3, "type": "assignment"}'
   ```

   **Generate a daily plan**

   ```bash
   curl -X POST http://localhost:8000/api/v1/assistant/daily-plan \
        -H "X-API-Key: <your key>" \
        -H "Content-Type: application/json" \
        -d '{
              "tasks": [
                {"title": "Assignment 1", "due_date": "2025-11-30", "estimated_hours": 3},
                {"title": "Lecture: Graph algorithms", "due_date": "2025-11-22", "estimated_hours": 2}
              ],
              "plan_date": "2025-11-20",
              "agent": "student"
            }'
   ```

   **Summarise an FAQ**

   ```bash
   curl -X POST http://localhost:8000/api/v1/assistant/faq-summary \
        -H "X-API-Key: <your key>" \
        -H "Content-Type: application/json" \
        -d '{
              "questions": [
                "What is the recurrence for merge sort?",
                "How do I choose the pivot in quicksort?",
                "Explain the master theorem"
              ],
              "agent": "prof"
            }'
   ```

   See `http://localhost:8000/docs` for a complete list of routes.

## Development

Use the scripts in `scripts/` to seed the database or create admin users.
Run tests with `pytest`:
```bash
pytest
```

## License

This project is provided as a template and does not include a software
license. You may use and modify it according to your needs.
