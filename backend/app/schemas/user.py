from pydantic import BaseModel, EmailStr
from typing import Optional
from app.db.models import UserRole

class UserBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    birth_date: Optional[str] = None
    bureau: Optional[str] = None
    role: UserRole = UserRole.NOTAIRE

class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    password: Optional[str] = None

class UserOut(UserBase):
    id: int
    is_active: int

    class Config:
        from_attributes = True
