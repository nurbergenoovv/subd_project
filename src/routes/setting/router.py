from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from . import functions as crud, models, schemas
from src.database import get_async_session  # Импорт асинхронной сессии

router = APIRouter(
    prefix="/setting",
    tags=["Settings"]
)

@router.post("/", response_model=schemas.SettingsResponse)
async def create_settings(settings: schemas.SettingsCreate, db: AsyncSession = Depends(get_async_session)):
    return await crud.create_settings(db=db, settings=settings)

@router.put("/{settings_id}", response_model=schemas.SettingsResponse)
async def update_settings(settings_id: int, settings: schemas.SettingsUpdate, db: AsyncSession = Depends(get_async_session)):
    db_settings = await crud.update_settings(db=db, settings_id=settings_id, settings=settings)
    if db_settings is None:
        raise HTTPException(status_code=404, detail="Settings not found")
    return db_settings

@router.delete("/{settings_id}", response_model=schemas.SettingsResponse)
async def delete_settings(settings_id: int, db: AsyncSession = Depends(get_async_session)):
    db_settings = await crud.delete_settings(db=db, settings_id=settings_id)
    if db_settings is None:
        raise HTTPException(status_code=404, detail="Settings not found")
    return db_settings

@router.get("/", response_model=schemas.SettingsResponse)
async def get_settings(db: AsyncSession = Depends(get_async_session)):
    settings = await crud.get_settings(db=db)
    if settings is None:
        raise HTTPException(status_code=404, detail="Settings not found")
    return settings


# @router.post('/ticket/{ticket_id}/telegram')
