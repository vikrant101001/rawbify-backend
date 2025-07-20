from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas.processing import ProcessDataResponse
from ..services.processing_service import ProcessingService
from ..config import settings
import io

router = APIRouter(prefix="/process-data", tags=["processing"])

@router.post("", response_model=ProcessDataResponse)
async def process_data(
    file: UploadFile = File(...),
    prompt: str = Form(...),
    userId: str = Form(...),
    db: Session = Depends(get_db)
):
    """Process uploaded file and return processed data"""
    
    # Validate file size
    if file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB.")
    
    # Validate file type
    file_extension = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
    if file_extension not in ['xlsx', 'xls', 'csv']:
        raise HTTPException(status_code=400, detail="Unsupported file type. Please upload Excel or CSV files.")
    
    # Read file content
    try:
        file_content = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")
    
    # Process the data
    result = ProcessingService.process_data(db, file_content, file.filename, prompt, userId)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return ProcessDataResponse(
        success=True,
        data=result["data"],
        processingSummary=result["processingSummary"],
        error=None
    ) 