from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.models.user import User
from src.schemas.user import UserCreate, UserResponse
from typing import List


async def create_user(db: AsyncSession, user: UserCreate) -> UserResponse:
    try:
        async with db as session:
            new_user = User(name=user.name, email=user.email)
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)
            return UserResponse.model_validate(new_user)
    except Exception as e:
        await db.rollback()
        raise e

async def get_user(db: AsyncSession, user_id: int) -> UserResponse:
    try: 
        async with db as session:
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if user is None:
                raise ValueError("User not found")
            return UserResponse.model_validate(user)
    except Exception as e:
        await db.rollback()
        raise e


async def get_all_users(db: AsyncSession) -> List[UserResponse]:
    try:
        async with db as session:
            result = await session.execute(select(User))
            users = result.scalars().all()
            return [UserResponse.model_validate(user) for user in users]
    except Exception as e:
        await db.rollback()
        raise e