from pydantic import BaseModel
from typing import Optional

class UserValidation(BaseModel):
    userId: str

class UserValidationResponse(BaseModel):
    allowed: bool
    success: bool
    error: Optional[str] = None 