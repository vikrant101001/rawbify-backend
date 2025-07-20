from pydantic import BaseModel
from typing import List, Optional

class ProcessDataRequest(BaseModel):
    prompt: str
    userId: str

class ProcessDataResponse(BaseModel):
    success: bool
    data: Optional[bytes] = None
    processingSummary: Optional[List[str]] = None
    error: Optional[str] = None 