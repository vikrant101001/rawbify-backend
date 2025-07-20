#!/usr/bin/env python3
"""
Script to add test users for development
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.user import User
from datetime import datetime

def add_test_users():
    """Add test users to the database"""
    db = SessionLocal()
    
    test_users = [
        {
            "email": "test@rawbify.com",
            "user_id": "test123",
            "trial_access_granted": True,
            "trial_access_date": datetime.utcnow()
        },
        {
            "email": "demo@rawbify.com", 
            "user_id": "demo456",
            "trial_access_granted": True,
            "trial_access_date": datetime.utcnow()
        },
        {
            "email": "trial@rawbify.com",
            "user_id": "trial789", 
            "trial_access_granted": True,
            "trial_access_date": datetime.utcnow()
        },
        {
            "email": "admin@rawbify.com",
            "user_id": "user_admin", 
            "trial_access_granted": True,
            "trial_access_date": datetime.utcnow()
        }
    ]
    
    try:
        for user_data in test_users:
            # Check if user already exists
            existing = db.query(User).filter(User.user_id == user_data["user_id"]).first()
            if existing:
                print(f"User {user_data['user_id']} already exists, skipping...")
                continue
            
            # Create new user
            new_user = User(**user_data)
            db.add(new_user)
            print(f"Added test user: {user_data['user_id']}")
        
        db.commit()
        print("Test users added successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"Error adding test users: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    add_test_users() 