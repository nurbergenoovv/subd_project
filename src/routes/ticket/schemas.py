from pydantic import BaseModel, root_validator, validator, Field
from typing import Optional
from datetime import datetime

class TicketCreate(BaseModel):
    full_name: str
    phone_number: str
    category_id: int
    language: Optional[str]

class TicketUpdate(BaseModel):
    status: str

    @validator('status')
    def validate_status(cls, v):
        if v not in ["wait", "invited", "completed", "skipped", "cancelled"]:
            raise ValueError("Invalid status")
        return v

class TicketOut(BaseModel):
    id: int
    full_name: str
    phone_number: str
    created_at: str
    category_id: int
    status: str
    number: str
    rate: Optional[int]
    worker_id: Optional[int]
    language: str
    token: str
    duration: Optional[float] = None

    @validator('created_at', pre=True)
    def format_datetime(cls, v):
        if isinstance(v, datetime):
            return v.strftime("%Y-%m-%d %H:%M:%S")
        return v

    class Config:
        from_attributes = True


class TicketFilter(BaseModel):
    date_filter: Optional[str] = Field(
        None, description="Options: 1_day, 1_week, 1_month", example="1_day"
    )