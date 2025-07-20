from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas.waitlist import WaitlistCreate, WaitlistResponse
from ..services.waitlist_service import WaitlistService

router = APIRouter(prefix="/waitlist", tags=["waitlist"])

@router.post("/join", response_model=WaitlistResponse)
async def join_waitlist(waitlist_data: WaitlistCreate, db: Session = Depends(get_db)):
    """Add email to waitlist"""
    result = WaitlistService.add_to_waitlist(db, waitlist_data.email)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return WaitlistResponse(
        success=True,
        message=result["message"],
        waitlist_count=result["waitlist_count"]
    )

@router.get("/stats", response_model=WaitlistResponse)
async def get_waitlist_stats(db: Session = Depends(get_db)):
    """Get waitlist statistics"""
    result = WaitlistService.get_waitlist_stats(db)
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])
    
    return WaitlistResponse(
        success=True,
        message=result["message"],
        waitlist_count=result["waitlist_count"]
    ) 