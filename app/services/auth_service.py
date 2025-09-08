"""
Authentication service for user signup and signin
"""
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from ..models.user import User
from ..schemas.user import UserSignup, UserSignin, AuthResponse, UserResponse
from ..utils.auth import hash_password, verify_password, create_access_token
import logging

logger = logging.getLogger(__name__)

class AuthService:
    
    @staticmethod
    def signup(db: Session, user_data: UserSignup) -> AuthResponse:
        """Create a new user account"""
        try:
            # Check if username already exists
            existing_user = db.query(User).filter(User.username == user_data.username).first()
            if existing_user:
                return AuthResponse(
                    success=False,
                    message="Username already exists"
                )
            
            # Hash the password
            password_hash = hash_password(user_data.password)
            
            # Create new user
            new_user = User(
                username=user_data.username,
                password_hash=password_hash,
                is_active=True,
                trial_access_granted=True  # Grant trial access by default
            )
            
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            # Create access token
            token = create_access_token(data={"sub": new_user.username, "user_id": str(new_user.id)})
            
            logger.info(f"✅ User created successfully: {user_data.username}")
            
            # Convert to dict and ensure all values are JSON serializable
            user_dict = {
                "id": str(new_user.id),
                "username": new_user.username,
                "created_at": new_user.created_at,
                "is_active": new_user.is_active,
                "trial_access_granted": new_user.trial_access_granted
            }
            
            return AuthResponse(
                success=True,
                message="Account created successfully",
                user=UserResponse(**user_dict),
                token=token
            )
            
        except IntegrityError as e:
            db.rollback()
            logger.error(f"❌ Database integrity error during signup: {e}")
            return AuthResponse(
                success=False,
                message="Username already exists"
            )
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error during signup: {e}")
            return AuthResponse(
                success=False,
                message="Failed to create account"
            )
    
    @staticmethod
    def signin(db: Session, user_data: UserSignin) -> AuthResponse:
        """Authenticate user and return token"""
        try:
            # Find user by username
            user = db.query(User).filter(User.username == user_data.username).first()
            
            if not user:
                return AuthResponse(
                    success=False,
                    message="Invalid username or password"
                )
            
            # Verify password
            if not verify_password(user_data.password, user.password_hash):
                return AuthResponse(
                    success=False,
                    message="Invalid username or password"
                )
            
            # Check if user is active
            if not user.is_active:
                return AuthResponse(
                    success=False,
                    message="Account is deactivated"
                )
            
            # Update last login
            user.last_login = datetime.utcnow()
            db.commit()
            
            # Create access token
            token = create_access_token(data={"sub": user.username, "user_id": str(user.id)})
            
            logger.info(f"✅ User signed in successfully: {user_data.username}")
            
            # Convert to dict and ensure all values are JSON serializable
            user_dict = {
                "id": str(user.id),
                "username": user.username,
                "created_at": user.created_at,
                "is_active": user.is_active,
                "trial_access_granted": user.trial_access_granted
            }
            
            return AuthResponse(
                success=True,
                message="Signed in successfully",
                user=UserResponse(**user_dict),
                token=token
            )
            
        except Exception as e:
            logger.error(f"❌ Error during signin: {e}")
            return AuthResponse(
                success=False,
                message="Failed to sign in"
            )
    
    @staticmethod
    def get_user_by_username(db: Session, username: str) -> User:
        """Get user by username"""
        return db.query(User).filter(User.username == username).first()
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> User:
        """Get user by ID"""
        return db.query(User).filter(User.id == user_id).first()
