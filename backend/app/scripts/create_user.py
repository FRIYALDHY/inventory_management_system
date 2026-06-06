import argparse
import asyncio

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.domain.enums import UserRole
from app.domain.models import User


async def create_user(email: str, full_name: str, password: str, role: UserRole) -> None:
    async with AsyncSessionLocal() as db:
        existing = await db.scalar(select(User.id).where(User.email == email.lower()))
        if existing:
            raise SystemExit(f"User with email {email} already exists")
        db.add(
            User(
                email=email.lower(),
                full_name=full_name,
                hashed_password=hash_password(password),
                role=role,
                is_active=True,
            )
        )
        await db.commit()
        print(f"Created {role.value} user: {email}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create ATA PIMS user")
    parser.add_argument("--email", required=True)
    parser.add_argument("--full-name", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--role", choices=[role.value for role in UserRole], required=True)
    args = parser.parse_args()
    asyncio.run(create_user(args.email, args.full_name, args.password, UserRole(args.role)))


if __name__ == "__main__":
    main()

