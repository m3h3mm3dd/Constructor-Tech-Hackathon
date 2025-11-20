"""
Analytics service stub.

Provides usage statistics for the backend. In this example the metrics
are hard-coded. You can replace this logic with database queries or
aggregations from a metrics backend such as Prometheus.
"""


async def get_usage_stats() -> dict:
    """Return usage statistics for the backend.

    Returns:
        dict: A dictionary of usage metrics.
    """
    # In a real implementation, gather metrics from the database or monitoring
    # infrastructure here.
    return {
        "messages_processed": 0,
        "active_users": 0,
        "agents_configured": 3,
    }