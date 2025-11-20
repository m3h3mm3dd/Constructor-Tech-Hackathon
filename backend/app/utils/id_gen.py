"""
Utility functions for generating unique identifiers.
"""

import uuid

def generate_id() -> str:
    """Generate a random hexadecimal ID using UUID4.

    Returns:
        str: A 32-character hexadecimal string.
    """
    return uuid.uuid4().hex
