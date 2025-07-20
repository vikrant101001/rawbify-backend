import pandas as pd
import io
import json
from sqlalchemy.orm import Session
from ..models.processing_job import ProcessingJob
from ..models.user import User
from datetime import datetime
import uuid

class ProcessingService:
    # Special admin user ID for testing
    ADMIN_USER_ID = "user_admin"
    
    @staticmethod
    def process_data(db: Session, file_content: bytes, file_name: str, prompt: str, user_id: str) -> dict:
        """Process uploaded file and add 'done' column"""
        try:
            # Special case: admin user always allowed
            if user_id == ProcessingService.ADMIN_USER_ID:
                # For admin user, skip database validation
                user_exists = True
            else:
                # Validate user exists
                user = db.query(User).filter(User.user_id == user_id, User.is_active == True).first()
                user_exists = user is not None
            
            if not user_exists:
                return {
                    "success": False,
                    "data": None,
                    "processingSummary": None,
                    "error": "Invalid user ID"
                }
            
            # Create processing job record
            job = ProcessingJob(
                user_id=user_id,
                file_name=file_name,
                file_size=len(file_content),
                prompt=prompt,
                status='processing'
            )
            db.add(job)
            db.commit()
            
            # Process the file
            try:
                # Read the file based on extension
                if file_name.lower().endswith('.csv'):
                    df = pd.read_csv(io.BytesIO(file_content))
                elif file_name.lower().endswith(('.xlsx', '.xls')):
                    df = pd.read_excel(io.BytesIO(file_content))
                else:
                    raise ValueError("Unsupported file format")
                
                # Add 'done' column
                df['done'] = 'done'
                
                # Convert back to CSV
                output_buffer = io.BytesIO()
                df.to_csv(output_buffer, index=False)
                output_buffer.seek(0)
                processed_data = output_buffer.getvalue()
                
                # Create processing summary
                processing_summary = [
                    f"Processed {len(df)} records",
                    "Added 'done' column",
                    "Converted to CSV format",
                    "Ready for download"
                ]
                
                # Update job status
                job.status = 'completed'
                job.completed_at = datetime.utcnow()
                job.processing_summary = json.dumps(processing_summary)  # Store as JSON string
                db.commit()
                
                return {
                    "success": True,
                    "data": processed_data,
                    "processingSummary": processing_summary,
                    "error": None
                }
                
            except Exception as e:
                # Update job status to failed
                job.status = 'failed'
                job.error_message = str(e)
                db.commit()
                
                return {
                    "success": False,
                    "data": None,
                    "processingSummary": None,
                    "error": f"File processing error: {str(e)}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "data": None,
                "processingSummary": None,
                "error": f"Processing error: {str(e)}"
            } 