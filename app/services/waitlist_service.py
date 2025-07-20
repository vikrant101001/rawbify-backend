from sqlalchemy.orm import Session
from ..models.waitlist import Waitlist
from ..schemas.waitlist import WaitlistCreate
from ..config import settings
import re

class WaitlistService:
    @staticmethod
    def add_to_waitlist(db: Session, email: str) -> dict:
        """Add email to waitlist"""
        try:
            # Check if email already exists
            existing = db.query(Waitlist).filter(Waitlist.email == email).first()
            if existing:
                return {
                    "success": False,
                    "message": "Email already on waitlist",
                    "waitlist_count": None
                }
            
            # Add new email to waitlist
            new_waitlist = Waitlist(email=email)
            db.add(new_waitlist)
            db.commit()
            
            # Get total count
            total_count = db.query(Waitlist).count()
            
            return {
                "success": True,
                "message": "Successfully added to waitlist",
                "waitlist_count": total_count
            }
            
        except Exception as e:
            db.rollback()
            return {
                "success": False,
                "message": f"Error adding to waitlist: {str(e)}",
                "waitlist_count": None
            }
    
    @staticmethod
    def get_waitlist_stats(db: Session) -> dict:
        """Get waitlist statistics"""
        try:
            total_count = db.query(Waitlist).count()
            return {
                "success": True,
                "message": "Waitlist stats retrieved",
                "waitlist_count": total_count
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error getting stats: {str(e)}",
                "waitlist_count": None
            } 