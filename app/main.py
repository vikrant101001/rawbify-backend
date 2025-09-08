from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .database import engine, Base
from .api import waitlist_router, user_router, processing_router, auth_router

# Create database tables (with error handling for Vercel)
try:
    if engine is not None:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
    else:
        print("⚠️ Database engine not available, skipping table creation")
except Exception as e:
    print(f"⚠️ Database table creation failed: {e}")

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Rawbify Backend API - Raw Data In. BI Ready Out."
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(waitlist_router, prefix=settings.API_V1_STR)
app.include_router(user_router, prefix=settings.API_V1_STR)
app.include_router(processing_router, prefix=settings.API_V1_STR)
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["authentication"])

@app.get("/")
async def root():
    return {
        "message": "Rawbify Backend API",
        "version": "1.0.0",
        "status": "running",
        "platform": "vercel"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/env-debug")
async def environment_debug():
    """Debug environment variables (masks sensitive data)"""
    import os
    
    return {
        "DATABASE_URL_SET": bool(os.getenv("DATABASE_URL")),
        "DATABASE_URL_TYPE": "pooling" if "pooler.supabase.com" in (os.getenv("DATABASE_URL", "")) else "direct" if "supabase.co" in (os.getenv("DATABASE_URL", "")) else "other",
        "DATABASE_URL_MASKED": (os.getenv("DATABASE_URL", ""))[:50] + "..." if os.getenv("DATABASE_URL") else "NOT_SET",
        "DB_HOST_SET": bool(os.getenv("DB_HOST")),
        "DB_HOST_VALUE": os.getenv("DB_HOST", "NOT_SET"),
        "SETTINGS_DATABASE_URL": settings.DATABASE_URL[:50] + "..." if settings.DATABASE_URL else "NOT_SET",
        "SETTINGS_DB_HOST": settings.DB_HOST or "NOT_SET",
        "OPENAI_KEY_SET": bool(settings.OPENAI_API_KEY)
    }

@app.post("/debug/signup")
async def debug_signup():
    """Debug signup process with detailed error info"""
    from sqlalchemy.orm import Session
    from .database import get_db
    from .services.auth_service import AuthService
    from .schemas.user import UserSignup
    
    try:
        # Test database connection
        db = next(get_db())
        
        # Test user creation with debug info
        test_user = UserSignup(username="debug_test_user", password="testpass123")
        
        # Try the signup process
        result = AuthService.signup(db, test_user)
        
        # Clean up test user if created
        if result.success and result.user:
            from .models.user import User
            user_to_delete = db.query(User).filter(User.username == "debug_test_user").first()
            if user_to_delete:
                db.delete(user_to_delete)
                db.commit()
        
        db.close()
        
        return {
            "status": "debug_complete",
            "signup_result": {
                "success": result.success,
                "message": result.message,
                "user_created": bool(result.user),
                "token_created": bool(result.token)
            },
            "database_accessible": True
        }
        
    except Exception as e:
        return {
            "status": "debug_error",
            "error": str(e),
            "error_type": type(e).__name__,
            "database_accessible": False
        }

@app.get("/db-simple")
async def simple_database_test():
    """Simple database connection test without SQLAlchemy"""
    import psycopg2
    from urllib.parse import urlparse
    
    try:
        # Parse DATABASE_URL if available
        if settings.DATABASE_URL and settings.DATABASE_URL != "sqlite:///./rawbify.db":
            # Parse the DATABASE_URL
            parsed = urlparse(settings.DATABASE_URL)
            conn = psycopg2.connect(
                host=parsed.hostname,
                port=parsed.port or 5432,
                database=parsed.path[1:],  # Remove leading slash
                user=parsed.username,
                password=parsed.password,
                connect_timeout=10
            )
        else:
            # Fallback to individual parameters
            conn = psycopg2.connect(
                host=settings.DB_HOST,
                port=settings.DB_PORT,
                database=settings.DB_NAME,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD,
                connect_timeout=10
            )
        
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
        return {
            "status": "success",
            "connection": "direct_psycopg2",
            "test_query": result,
            "message": "Direct connection works!"
        }
        
    except Exception as e:
        # Show which connection method was attempted
        if settings.DATABASE_URL and settings.DATABASE_URL != "sqlite:///./rawbify.db":
            from urllib.parse import urlparse
            parsed = urlparse(settings.DATABASE_URL)
            connection_info = {
                "method": "DATABASE_URL_parsed",
                "host": parsed.hostname,
                "port": parsed.port or 5432,
                "database": parsed.path[1:] if parsed.path else "postgres",
                "user": parsed.username
            }
        else:
            connection_info = {
                "method": "individual_parameters",
                "host": settings.DB_HOST,
                "port": settings.DB_PORT,
                "database": settings.DB_NAME,
                "user": settings.DB_USER
            }
            
        return {
            "status": "error",
            "connection": "direct_psycopg2",
            "error": str(e),
            "error_type": type(e).__name__,
            **connection_info
        }

@app.get("/db-health")
async def database_health_check():
    """Check database connection and tables"""
    from sqlalchemy import text
    from .database import engine, get_db
    
    # Debug info about connection
    debug_info = {
        "database_url_set": bool(settings.DATABASE_URL and settings.DATABASE_URL != "sqlite:///./rawbify.db"),
        "database_url_type": "postgresql" if settings.DATABASE_URL.startswith("postgresql") else "sqlite" if "sqlite" in settings.DATABASE_URL else "other",
        "database_url_masked": settings.DATABASE_URL.replace(settings.DB_PASSWORD, "***") if settings.DB_PASSWORD else settings.DATABASE_URL[:50] + "...",
        "db_host": settings.DB_HOST,
        "db_port": settings.DB_PORT,
        "db_name": settings.DB_NAME,
        "db_user": settings.DB_USER,
        "db_password_set": bool(settings.DB_PASSWORD)
    }
    
    try:
        # Test database connection
        with engine.connect() as connection:
            # Test basic connection
            result = connection.execute(text("SELECT 1 as test"))
            test_value = result.fetchone()[0]
            
            # Check if our tables exist
            tables_result = connection.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE 'r_%'
                ORDER BY table_name
            """))
            tables = [row[0] for row in tables_result.fetchall()]
            
            # Check user count if table exists
            user_count = 0
            if 'r_users' in tables:
                user_result = connection.execute(text("SELECT COUNT(*) FROM r_users"))
                user_count = user_result.fetchone()[0]
            
            return {
                "status": "healthy",
                "database": "connected",
                "test_query": test_value,
                "tables_found": tables,
                "user_count": user_count,
                **debug_info
            }
            
    except Exception as e:
        return {
            "status": "error",
            "database": "disconnected", 
            "error": str(e),
            "error_type": type(e).__name__,
            **debug_info
        } 