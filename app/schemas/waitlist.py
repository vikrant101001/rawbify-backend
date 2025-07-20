from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class WaitlistCreate(BaseModel):
    email: EmailStr

class WaitlistResponse(BaseModel):
    success: bool
    message: str
    waitlist_count: Optional[int] = None

    class Config:
        from_attributes = True 