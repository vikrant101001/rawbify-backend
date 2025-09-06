from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Legacy validation schemas (keep for backward compatibility)
class UserValidation(BaseModel):
    userId: str

class UserValidationResponse(BaseModel):
    allowed: bool
    success: bool
    error: Optional[str] = None

# New authentication schemas
class UserSignup(BaseModel):
    username: str
    password: str

class UserSignin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    created_at: datetime
    is_active: bool
    trial_access_granted: bool
    
    class Config:
        from_attributes = True

class AuthResponse(BaseModel):
    success: bool
    message: str
    user: Optional[UserResponse] = None
    token: Optional[str] = None

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[str] = None 