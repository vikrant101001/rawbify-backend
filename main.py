# Vercel entry point
import os
import sys

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app.main import app
    # For Vercel deployment
    handler = app
except Exception as e:
    print(f"Error importing app: {e}")
    # Create a simple error app if main app fails
    from fastapi import FastAPI
    
    error_app = FastAPI()
    
    @error_app.get("/")
    async def error_root():
        return {
            "error": "App failed to initialize",
            "message": str(e),
            "status": "error"
        }
    
    handler = error_app

# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
