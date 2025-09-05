import sys
import os

# Add the parent directory to Python path so we can import our app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the FastAPI app
from app.main import app

# Vercel expects the app to be available as a module-level variable
# No need for additional wrapper functions
