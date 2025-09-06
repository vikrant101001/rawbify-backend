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

@app.get("/db-health")
async def database_health_check():
    """Check database connection and tables"""
    from sqlalchemy import text
    from .database import engine, get_db
    
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
                "database_url_set": bool(settings.DATABASE_URL and settings.DATABASE_URL != "sqlite:///./rawbify.db")
            }
            
    except Exception as e:
        return {
            "status": "error",
            "database": "disconnected",
            "error": str(e),
            "database_url_set": bool(settings.DATABASE_URL and settings.DATABASE_URL != "sqlite:///./rawbify.db"),
            "database_url_type": "postgresql" if settings.DATABASE_URL.startswith("postgresql") else "other"
        } 