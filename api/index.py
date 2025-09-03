# Vercel entry point
from app.main import app

# This is required for Vercel to recognize the FastAPI app
handler = app
