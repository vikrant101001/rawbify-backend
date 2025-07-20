from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas.user import UserValidation, UserValidationResponse
from ..services.user_service import UserService

router = APIRouter(prefix="/validate-user", tags=["user"])

@router.post("", response_model=UserValidationResponse)
async def validate_user(user_data: UserValidation, db: Session = Depends(get_db)):
    """Validate user ID for trial access"""
    result = UserService.validate_user_id(db, user_data.userId)
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return UserValidationResponse(
        allowed=result["allowed"],
        success=result["success"],
        error=result.get("error")  # Use .get() to safely handle None values
    ) 