"""Version 1 API package.

This package exports versioned API routers for inclusion in the FastAPI
application. Importing modules here makes it easier to reference
individual routers when constructing the app in ``main.py``.
"""

# Expose routers at the package level for convenient import
from . import chat_routes  # noqa: F401
from . import stream_routes  # noqa: F401
from . import agent_routes  # noqa: F401
from . import admin_routes  # noqa: F401
from . import rag_routes  # noqa: F401
from . import assistant_routes  # noqa: F401
from . import course_routes  # noqa: F401