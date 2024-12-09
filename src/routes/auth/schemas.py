from typing import Optional

from pydantic import BaseModel

class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    is_admin: bool
    window: Optional[int]
    category_id: Optional[int]
    admin_token: str

class GetToken(BaseModel):
    token: str

class UserOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    is_admin: bool
    window: Optional[int]
    token: str
    category_id: Optional[int]

    class Config:
        from_attributes = True


class ForgetPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class UserUpdate(BaseModel):
    first_name: str
    last_name: str
    email: str
    window: int
    category_id: Optional[int]