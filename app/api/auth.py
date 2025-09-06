"""
Authentication API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas.user import UserSignup, UserSignin, AuthResponse
from ..services.auth_service import AuthService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/signup", response_model=AuthResponse)
async def signup(user_data: UserSignup, db: Session = Depends(get_db)):
    """
    Create a new user account
    
    - **username**: Unique username (3-50 characters)
    - **password**: Password (minimum 6 characters)
    """
    # Basic validation
    if len(user_data.username) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username must be at least 3 characters long"
        )
    
    if len(user_data.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long"
        )
    
    result = AuthService.signup(db, user_data)
    
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.message
        )
    
    return result

@router.post("/signin", response_model=AuthResponse)
async def signin(user_data: UserSignin, db: Session = Depends(get_db)):
    """
    Sign in with username and password
    
    - **username**: Your username
    - **password**: Your password
    """
    result = AuthService.signin(db, user_data)
    
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result.message
        )
    
    return result

@router.get("/me")
async def get_current_user(db: Session = Depends(get_db)):
    """
    Get current user information (requires authentication)
    Note: This is a placeholder - you'll need to implement JWT middleware later
    """
    return {
        "message": "This endpoint will return current user info after implementing JWT middleware",
        "status": "placeholder"
    }
