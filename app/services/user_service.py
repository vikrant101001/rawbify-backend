from sqlalchemy.orm import Session
from ..models.user import User
from datetime import datetime

class UserService:
    # Special admin user ID for testing
    ADMIN_USER_ID = "user_admin"
    
    @staticmethod
    def validate_user_id(db: Session, user_id: str) -> dict:
        """Validate if user_id exists and is active"""
        try:
            # Special case: admin user always allowed
            if user_id == UserService.ADMIN_USER_ID:
                return {
                    "allowed": True,
                    "success": True,
                    "error": None
                }
            
            user = db.query(User).filter(
                User.user_id == user_id,
                User.is_active == True
            ).first()
            
            if user:
                # Update access count
                user.access_count += 1
                db.commit()
                
                return {
                    "allowed": True,
                    "success": True,
                    "error": None
                }
            else:
                return {
                    "allowed": False,
                    "success": True,
                    "error": "Invalid User ID"
                }
                
        except Exception as e:
            return {
                "allowed": False,
                "success": False,
                "error": f"Validation error: {str(e)}"
            }
    
    @staticmethod
    def create_trial_user(db: Session, email: str, user_id: str) -> dict:
        """Create a new trial user"""
        try:
            # Check if user_id already exists
            existing = db.query(User).filter(User.user_id == user_id).first()
            if existing:
                return {
                    "success": False,
                    "message": "User ID already exists"
                }
            
            # Create new user
            new_user = User(
                email=email,
                user_id=user_id,
                trial_access_granted=True,
                trial_access_date=datetime.utcnow()
            )
            db.add(new_user)
            db.commit()
            
            return {
                "success": True,
                "message": "Trial user created successfully"
            }
            
        except Exception as e:
            db.rollback()
            return {
                "success": False,
                "message": f"Error creating user: {str(e)}"
            } 