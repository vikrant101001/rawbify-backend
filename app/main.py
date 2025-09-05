from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .database import engine, Base
from .api import waitlist_router, user_router, processing_router

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