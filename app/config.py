import os
import logging
from dotenv import load_dotenv

# Configure logging for config
logger = logging.getLogger(__name__)

# Load environment variables
logger.info("🔧 Loading environment variables from .env file")
load_dotenv()
logger.info(f"🔧 Environment loaded - Current working directory: {os.getcwd()}")
logger.info(f"🔧 .env file exists: {os.path.exists('.env')}")
logger.info(f"🔧 OPENAI_API_KEY from os.getenv: {bool(os.getenv('OPENAI_API_KEY'))}")

class Settings:
    def __init__(self):
        # Database - Handle multiple connection formats
        self.DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./rawbify.db")
        
        # Alternative: Individual database parameters (for debugging)
        self.DB_HOST: str = os.getenv("DB_HOST", "")
        self.DB_PORT: str = os.getenv("DB_PORT", "5432")
        self.DB_NAME: str = os.getenv("DB_NAME", "postgres")
        self.DB_USER: str = os.getenv("DB_USER", "postgres")
        self.DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
        
        # Priority: Use DATABASE_URL if set, otherwise build from individual components
        if self.DATABASE_URL and self.DATABASE_URL != "sqlite:///./rawbify.db":
            # DATABASE_URL is already set, use it as-is
            logger.info(f"🔧 Using DATABASE_URL: {self.DATABASE_URL[:50]}...")
        elif self.DB_HOST and self.DB_PASSWORD:
            # Build from individual components as fallback
            self.DATABASE_URL = f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            logger.info(f"🔧 Built DATABASE_URL from components: {self.DB_HOST}:{self.DB_PORT}")
        else:
            logger.warning("🔧 No database configuration found, using SQLite")
        
        # Convert Railway's DATABASE_URL to SQLAlchemy format if needed
        if self.DATABASE_URL.startswith("postgres://"):
            self.DATABASE_URL = self.DATABASE_URL.replace("postgres://", "postgresql://", 1)
        
        # API Settings
        self.API_V1_STR: str = "/api"
        self.PROJECT_NAME: str = "Rawbify Backend"
    
    # CORS - Support multiple deployment platforms
    CORS_ORIGINS: list = [
        "http://localhost:3000",  # Frontend dev
        "http://localhost:3001",
        "https://rawbify.com",    # Production frontend
        "https://rawbify-frontend.railway.app",  # Railway frontend
        "https://rawbify.vercel.app",  # Vercel frontend
        "https://*.vercel.app",   # All Vercel deployments
        "https://*.railway.app",  # All Railway deployments
    ]
    
    # File Upload
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: list = [".xlsx", ".xls", ".csv"]
    
    # Email (SendGrid or Gmail SMTP)
    SENDGRID_API_KEY: str = os.getenv("SENDGRID_API_KEY", "")
    FROM_EMAIL: str = os.getenv("FROM_EMAIL", "noreply@rawbify.com")
    
    # Gmail SMTP
    GMAIL_USER: str = os.getenv("GMAIL_USER", "")
    GMAIL_APP_PASSWORD: str = os.getenv("GMAIL_APP_PASSWORD", "")
    
    # OpenAI API for AI Processing
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # JWT Secret Key for authentication
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-super-secret-jwt-key-change-this-in-production")
    
    def __init__(self):
        logger.info(f"🔧 Settings initialized - OPENAI_API_KEY: {bool(self.OPENAI_API_KEY)}")
        if self.OPENAI_API_KEY:
            logger.info(f"🔧 OPENAI_API_KEY length: {len(self.OPENAI_API_KEY)}")
            logger.info(f"🔧 OPENAI_API_KEY preview: {self.OPENAI_API_KEY[:10]}...")
        else:
            logger.warning("⚠️ OPENAI_API_KEY is empty or None")
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

settings = Settings() 