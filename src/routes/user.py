from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from src.services.users.user import create_user, get_user, get_all_users
from src.schemas.user import UserCreate, UserResponse
from src.db.config import get_async_session

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/users", response_model=UserResponse)
async def create_user_route(user: UserCreate, db: AsyncSession = Depends(get_async_session)):
    try:
        return await create_user(db, user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}", response_model=UserResponse)
async def get_user_route(user_id: int, db: AsyncSession = Depends(get_async_session)):
    try:
        return await get_user(db, user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[UserResponse])
async def get_all_users_route(db: AsyncSession = Depends(get_async_session)):
    try:
        return await get_all_users(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))