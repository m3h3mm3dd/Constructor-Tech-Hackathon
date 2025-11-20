"""
Admin user creation script.

This script demonstrates how you might create an administrative user in the
database. It is provided as a placeholder and does not implement secure
password handling. Replace the password hashing and storage mechanism
before use in production.
"""

import asyncio

from app.db.session import async_session
from app.db.models import User


async def create_admin(email: str, password: str) -> None:
    async with async_session() as session:
        admin = User(email=email, hashed_password=password, is_active=True)
        session.add(admin)
        await session.commit()
        print(f"Admin user {email} created")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Create an admin user")
    parser.add_argument("email", type=str, help="Admin email address")
    parser.add_argument("password", type=str, help="Admin password")
    args = parser.parse_args()
    asyncio.run(create_admin(args.email, args.password))