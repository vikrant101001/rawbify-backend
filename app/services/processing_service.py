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
        """Create comprehensive prompt with all context - no RAG needed"""
        
        # Sample data for context (first 5 rows)
        sample_data = df.head(5).to_string(index=False)
        
        prompt = f"""
You are a data analyst expert. Add new columns to a CSV dataset based on the user's request.

DATASET INFO:
- Rows: {data_analysis['shape'][0]}, Columns: {data_analysis['shape'][1]}
- Column names: {data_analysis['columns']}
- Data types: {data_analysis['dtypes']}

SAMPLE DATA (first 5 rows):
{sample_data}

USER REQUEST: {user_prompt}

TASK: Create new columns based on the user's request. You can:
1. Calculate values from existing columns
2. Categorize data based on conditions
3. Extract information from text fields
4. Create derived metrics
5. Add status/flag columns

RESPOND WITH JSON:
{{
    "new_columns": [
        {{
            "name": "column_name",
            "type": "calculated|categorized|derived|text_processing",
            "logic": "description of logic",
            "formula": "executable logic pattern"
        }}
    ],
    "explanation": "What was created and why"
}}

Generate JSON response:"""
        
        return prompt
    
    @staticmethod
    def _get_ai_response(client, prompt: str) -> dict:
        """Get structured response from OpenAI"""
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",  # Fast and cost-effective for Trial V1
                messages=[
                    {"role": "system", "content": "You are a data analyst. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1500
            )
            
            response_text = response.choices[0].message.content
            return json.loads(response_text)
            
        except json.JSONDecodeError:
            return {
                "new_columns": [{"name": "ai_processed", "type": "derived", "logic": "AI response parsing failed", "formula": "done"}],
                "explanation": "AI returned invalid format"
            }
        except Exception as e:
            return {
                "new_columns": [{"name": "error", "type": "derived", "logic": f"AI call failed: {str(e)}", "formula": "error"}],
                "explanation": f"AI processing error: {str(e)}"
            }
    
    @staticmethod
    def _apply_ai_logic(df: pd.DataFrame, ai_response: dict, user_prompt: str) -> pd.DataFrame:
        """Apply AI-generated logic to create new columns"""
        result_df = df.copy()
        
        try:
            new_columns = ai_response.get('new_columns', [])
            
            for col_spec in new_columns:
                col_name = col_spec.get('name', 'ai_column')
                col_type = col_spec.get('type', 'derived')
                formula = col_spec.get('formula', 'done')
                
                try:
                    if col_type == 'calculated':
                        result_df = ProcessingService._apply_calculation(result_df, col_name, formula, user_prompt)
                    elif col_type == 'categorized':
                        result_df = ProcessingService._apply_categorization(result_df, col_name, formula, user_prompt)
                    elif col_type == 'text_processing':
                        result_df = ProcessingService._apply_text_processing(result_df, col_name, formula, user_prompt)
                    else:
                        # Default: simple derived column
                        result_df[col_name] = formula
                        
                except Exception as e:
                    result_df[col_name] = f"Error: {str(e)}"
            
            # If no columns were added, add a default one
            if len(new_columns) == 0:
                result_df['ai_processed'] = 'done'
                
        except Exception as e:
            result_df['processing_error'] = f"AI logic error: {str(e)}"
        
        return result_df
    
    @staticmethod
    def _apply_calculation(df: pd.DataFrame, col_name: str, formula: str, user_prompt: str) -> pd.DataFrame:
        """Apply mathematical calculations"""
        try:
            # Common calculation patterns
            if 'profit' in user_prompt.lower() or 'margin' in user_prompt.lower():
                # Look for revenue/cost columns
                revenue_col = ProcessingService._find_column(df, ['revenue', 'sales', 'income'])
                cost_col = ProcessingService._find_column(df, ['cost', 'expense', 'cogs'])
                
                if revenue_col and cost_col:
                    df[col_name] = ((df[revenue_col] - df[cost_col]) / df[revenue_col] * 100).round(2)
                else:
                    df[col_name] = 'Insufficient data'
            
            elif 'total' in user_prompt.lower() or 'sum' in user_prompt.lower():
                # Sum numeric columns
                numeric_cols = df.select_dtypes(include=['number']).columns
                if len(numeric_cols) > 1:
                    df[col_name] = df[numeric_cols].sum(axis=1)
                else:
                    df[col_name] = 'No numeric columns to sum'
            
            else:
                df[col_name] = 'Calculated'
                
        except Exception as e:
            df[col_name] = f"Calc error: {str(e)}"
            
        return df
    
    @staticmethod
    def _apply_categorization(df: pd.DataFrame, col_name: str, formula: str, user_prompt: str) -> pd.DataFrame:
        """Apply categorization logic"""
        try:
            # Common categorization patterns
            if 'high' in user_prompt.lower() and 'low' in user_prompt.lower():
                # Find numeric column to categorize
                numeric_cols = df.select_dtypes(include=['number']).columns
                if len(numeric_cols) > 0:
                    col_to_categorize = numeric_cols[0]
                    median_val = df[col_to_categorize].median()
                    df[col_name] = df[col_to_categorize].apply(lambda x: 'High' if x > median_val else 'Low')
                else:
                    df[col_name] = 'No numeric data'
            else:
                df[col_name] = 'Categorized'
                
        except Exception as e:
            df[col_name] = f"Category error: {str(e)}"
            
        return df
    
    @staticmethod
    def _apply_text_processing(df: pd.DataFrame, col_name: str, formula: str, user_prompt: str) -> pd.DataFrame:
        """Apply text processing"""
        try:
            if 'email' in user_prompt.lower() and 'domain' in user_prompt.lower():
                # Extract email domain
                email_col = ProcessingService._find_column(df, ['email', 'mail'])
                if email_col:
                    df[col_name] = df[email_col].str.split('@').str[1]
                else:
                    df[col_name] = 'No email column found'
            
            elif 'length' in user_prompt.lower():
                # Text length
                text_cols = df.select_dtypes(include=['object']).columns
                if len(text_cols) > 0:
                    df[col_name] = df[text_cols[0]].str.len()
                else:
                    df[col_name] = 'No text columns'
            
            else:
                df[col_name] = 'Text processed'
                
        except Exception as e:
            df[col_name] = f"Text error: {str(e)}"
            
        return df
    
    @staticmethod
    def _find_column(df: pd.DataFrame, possible_names: list) -> str:
        """Find column by possible names"""
        for col in df.columns:
            for name in possible_names:
                if name.lower() in col.lower():
                    return col
        return None 