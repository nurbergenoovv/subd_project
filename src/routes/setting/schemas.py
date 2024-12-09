from pydantic import BaseModel
from datetime import datetime, time


class SettingsCreate(BaseModel):
    fromm: time
    to: time


class SettingsUpdate(BaseModel):
    fromm: time
    to: time


class SettingsDelete(BaseModel):
    id: int


class SettingsResponse(BaseModel):
    id: int
    permission: bool
    fromm: str
    to: str

    class Config:
        from_attributes = True
