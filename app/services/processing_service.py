import pandas as pd
import io
import json
from sqlalchemy.orm import Session
from ..models.processing_job import ProcessingJob
from ..models.user import User
from datetime import datetime
import uuid
# AI Processing imports
import openai
from ..config import settings

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
                
                # Validate file size (Trial V1 limit: 1000 rows)
                if len(df) > 1000:
                    raise ValueError("File too large. Maximum 1000 rows allowed for Trial V1.")
                
                # Process with AI (replaces simple 'done' column)
                processed_df, ai_summary = ProcessingService._process_with_ai(df, prompt)
                
                # Convert back to CSV
                output_buffer = io.BytesIO()
                processed_df.to_csv(output_buffer, index=False)
                output_buffer.seek(0)
                processed_data = output_buffer.getvalue()
                
                # Create processing summary
                processing_summary = [
                    f"Processed {len(df)} records with AI",
                    f"User request: {prompt}",
                    f"AI processing: {ai_summary}",
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
    
    @staticmethod
    def _process_with_ai(df: pd.DataFrame, user_prompt: str):
        """
        Core AI processing - No RAG needed for small datasets
        Returns processed DataFrame and summary
        """
        try:
            # Initialize OpenAI client
            if not settings.OPENAI_API_KEY:
                # Fallback: just add 'done' column if no API key
                df['done'] = 'done'
                return df, "No AI key configured - added 'done' column"
            
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            
            # Step 1: Analyze data structure
            data_analysis = ProcessingService._analyze_data(df)
            
            # Step 2: Create AI prompt with full context
            ai_prompt = ProcessingService._create_ai_prompt(data_analysis, user_prompt, df)
            
            # Step 3: Get AI response
            ai_response = ProcessingService._get_ai_response(client, ai_prompt)
            
            # Step 4: Apply AI logic to create new columns
            processed_df = ProcessingService._apply_ai_logic(df, ai_response, user_prompt)
            
            return processed_df, ai_response.get('explanation', 'AI processing completed')
            
        except Exception as e:
            # Fallback: add 'done' column if AI fails
            df['done'] = f'AI Error: {str(e)}'
            return df, f"AI processing failed: {str(e)}"
    
    @staticmethod
    def _analyze_data(df: pd.DataFrame) -> dict:
        """Analyze CSV structure for AI context"""
        return {
            "shape": df.shape,
            "columns": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "sample_data": df.head(3).to_dict('records'),
            "null_counts": df.isnull().sum().to_dict(),
            "unique_counts": df.nunique().to_dict()
        }
    
    @staticmethod
    def _create_ai_prompt(data_analysis: dict, user_prompt: str, df: pd.DataFrame) -> str:
        """Create prompt for AI to generate executable Python code"""
        
        # Sample data for context (first 5 rows)
        sample_data = df.head(5).to_string(index=False)
        
        prompt = f"""
You are a Python/Pandas expert. You will receive a CSV dataset and a user request to add new columns.

DATASET INFO:
- Rows: {data_analysis['shape'][0]}, Columns: {data_analysis['shape'][1]}
- Column names: {data_analysis['columns']}
- Data types: {data_analysis['dtypes']}

SAMPLE DATA (first 5 rows):
{sample_data}

USER REQUEST: {user_prompt}

TASK: Generate Python pandas code to add the requested column(s) to the dataframe.

RULES:
1. The dataframe variable is called 'df'
2. Only use pandas operations
3. Handle missing/null values gracefully
4. Your code will be executed directly
5. Return only the executable code, no explanations

EXAMPLE:
User: "add profit margin column"
Code: df['profit_margin'] = ((df['revenue'] - df['cost']) / df['revenue'] * 100).round(2)

USER REQUEST: {user_prompt}
PYTHON CODE:"""
        
        return prompt
    
    @staticmethod
    def _get_ai_response(client, prompt: str) -> dict:
        """Get Python code from OpenAI"""
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",  # Fast and cost-effective for Trial V1
                messages=[
                    {"role": "system", "content": "You are a Python/pandas expert. Generate only executable pandas code. No explanations, no markdown, just pure Python code."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            code = response.choices[0].message.content.strip()
            
            # Clean up the code (remove markdown if any)
            if code.startswith("```python"):
                code = code.replace("```python", "").replace("```", "").strip()
            elif code.startswith("```"):
                code = code.replace("```", "").strip()
            
            return {
                "code": code,
                "explanation": "AI generated pandas code"
            }
            
        except Exception as e:
            return {
                "code": "df['ai_error'] = 'AI failed'",
                "explanation": f"AI processing error: {str(e)}"
            }
    
    @staticmethod
    def _apply_ai_logic(df: pd.DataFrame, ai_response: dict, user_prompt: str) -> pd.DataFrame:
        """Execute AI-generated Python code"""
        result_df = df.copy()
        
        try:
            code = ai_response.get('code', '')
            
            if not code or code.strip() == '':
                result_df['ai_processed'] = 'No code generated'
                return result_df
            
            # Execute the AI-generated code
            # Create a safe execution environment
            import numpy as np
            exec_globals = {
                'df': result_df,
                'pd': pd,
                'np': np,
                '__builtins__': {
                    'len': len,
                    'str': str,
                    'int': int,
                    'float': float,
                    'round': round,
                    'max': max,
                    'min': min,
                    'sum': sum,
                }
            }
            
            # Execute the code
            exec(code, exec_globals)
            
            # Get the modified dataframe
            result_df = exec_globals['df']
            
        except Exception as e:
            # If code execution fails, add error column
            result_df['execution_error'] = f"Code error: {str(e)}"
        
        return result_df
 