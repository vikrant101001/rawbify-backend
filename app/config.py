import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Database - Using SQLite for development
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./rawbify.db")
    
    # API Settings
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "Rawbify Backend"
    
    # CORS
    CORS_ORIGINS: list = [
        "http://localhost:3000",  # Frontend dev
        "http://localhost:3001",
        "https://rawbify.com",    # Production frontend
    ]
    
    # File Upload
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: list = [".xlsx", ".xls", ".csv"]
    
    # Email (SendGrid)
    SENDGRID_API_KEY: str = os.getenv("SENDGRID_API_KEY", "")
    FROM_EMAIL: str = os.getenv("FROM_EMAIL", "noreply@rawbify.com")
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

settings = Settings() 