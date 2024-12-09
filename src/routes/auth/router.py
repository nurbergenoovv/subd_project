import json

from fastapi import Depends, HTTPException, status, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from src import database
from src.routes.auth import models, schemas, auth
from typing import AsyncGenerator
from fastapi import APIRouter

from src.routes.auth.auth import decode_nextauth_session, get_google_user_info, get_user_by_email
from src.routes.auth.models import User
from src.routes.category.models import Category
from src.utils.mail import send_new_pass, send_pass

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with database.async_session_maker() as session:
        yield session

@router.post("/register/", response_model=schemas.UserOut)
async def register(request: Request, user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    data = await request.json()

    if user.is_admin is False:
        if user.category_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category ID is required.",
            )

        if user.admin_token is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
            )
        admin_data: schemas.UserOut = await auth.get_current_user(db, user.admin_token)
        if admin_data.is_admin is False:
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions",
            )

    # Проверяем, существует ли категория с данным category_id
    if user.category_id is not None:
        category = await db.execute(select(Category).where(Category.id == user.category_id))
        category = category.scalars().first()
        if not category:
            raise HTTPException(status_code=400, detail="Category not found")

    db_user = await auth.get_user_by_email(db, user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    password = auth.create_random_pass()
    hashed_password = auth.get_password_hash(password)
    token = auth.create_token()
    db_user = models.User(email=user.email, hashed_password=hashed_password, token=token, first_name=user.first_name, window=user.window, last_name=user.last_name, is_admin=user.is_admin, category_id=user.category_id)
    db.add(db_user)
    await send_pass(user.email, password, user.window, user.first_name)
    await db.commit()
    await db.refresh(db_user)
    return db_user

@router.post("/login", response_model=schemas.UserOut)
async def login_for_access_token(request: Request, db: AsyncSession = Depends(get_db)):
    data = await request.json()
    email = data.get("email")
    password = data.get('password')
    user1 = await get_user_by_email(db, email)
    if user1 is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this email does not exist",
        )
    user = await auth.authenticate_user(db, email, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password",
        )
    # Create a new token for the user
    token = auth.create_token()
    user.token = token
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login/google", response_model=schemas.UserOut)
async def login_for_access_token_google(request: Request, db: AsyncSession = Depends(get_db)):
    data = await request.json()
    token = data.get("token")
    google = decode_nextauth_session(token)
    if not google:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email does not exist",
        )
    user = await get_user_by_email(db, google.get("email"))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this email does not exist",
        )
    token = auth.create_token()
    user.token = token
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/", response_model=schemas.UserOut)
async def read_users_me(request: Request, db: AsyncSession = Depends(get_db)):
    data = await request.json()
    token = data.get("token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token not found",
        )

    current_user = await auth.get_user(db, token)

    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User does not exist",
        )
    return current_user

@router.get("/{user_id}", response_model=schemas.UserOut)
async def read_user(
        user_id: int,
        db: AsyncSession = Depends(get_db)
):
    user = await auth.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User does not exist"
        )
    return user


@router.put("/{user_id}", response_model=schemas.UserOut)
async def update_user(
        request: Request,
        user_id: int,
        updated_user: schemas.UserUpdate,
        db: AsyncSession = Depends(get_db),
):
    data = await request.json()
    admin_token = data.get("admin_token")
    if not admin_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token not found",
        )
    admin: schemas.UserOut = await auth.get_user(db, admin_token)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User does not exist",
        )
    if admin.is_admin is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User does not exist",
        )

    for key, value in updated_user.dict(exclude_unset=True).items():
        setattr(user, key, value)

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
        request: Request,
        user_id: int,
        db: AsyncSession = Depends(get_db),
):
    data = await request.json()
    admin_token = data.get("admin_token")
    if not admin_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token not found",
        )
    admin: schemas.UserOut = await auth.get_user(db, admin_token)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User does not exist",
        )
    if admin.is_admin is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User does not exist",
        )

    await db.delete(user)
    await db.commit()
    return {"message": "User deleted successfully"}

@router.post("/forget-password")
async def forget_password(request: schemas.ForgetPasswordRequest, db: AsyncSession = Depends(get_db)):
    reset_token = await auth.create_reset_token(db, request.email)
    return {"reset_token": reset_token}

@router.post("/reset-password")
async def reset_password(request: schemas.ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    user = await auth.verify_reset_token(db, request.token)
    user.hashed_password = auth.get_password_hash(request.new_password)
    user.reset_token = None
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return {"message": "Password reset successful"}