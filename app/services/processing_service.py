import pandas as pd
import io
import json
import logging
from sqlalchemy.orm import Session
from ..models.processing_job import ProcessingJob
from ..models.user import User
from datetime import datetime
import uuid
# AI Processing imports
import openai
from ..config import settings
from .ai_prompts import AIPrompts

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProcessingService:
    # Special admin user ID for testing
    ADMIN_USER_ID = "user_admin"
    
    @staticmethod
    def process_data(db: Session, file_content: bytes, file_name: str, prompt: str, user_id: str) -> dict:
        """Process uploaded file and add 'done' column"""
        logger.info(f"🚀 Starting data processing for user: {user_id}, file: {file_name}")
        logger.info(f"📝 User prompt: {prompt}")
        logger.info(f"📊 File size: {len(file_content)} bytes")
        
        try:
            # Special case: admin user always allowed
            if user_id == ProcessingService.ADMIN_USER_ID:
                logger.info("👑 Admin user detected - skipping validation")
                user_exists = True
            else:
                logger.info(f"🔍 Validating user: {user_id}")
                # Validate user exists
                user = db.query(User).filter(User.user_id == user_id, User.is_active == True).first()
                user_exists = user is not None
                logger.info(f"✅ User validation result: {user_exists}")
            
            if not user_exists:
                logger.error(f"❌ Invalid user ID: {user_id}")
                return {
                    "success": False,
                    "data": None,
                    "processingSummary": None,
                    "error": "Invalid user ID"
                }
            
            # Create processing job record
            logger.info("📋 Creating processing job record")
            job = ProcessingJob(
                user_id=user_id,
                file_name=file_name,
                file_size=len(file_content),
                prompt=prompt,
                status='processing'
            )
            db.add(job)
            db.commit()
            logger.info(f"✅ Job created with ID: {job.id}")
            
            # Process the file
            try:
                logger.info("📖 Reading file content")
                # Read the file based on extension
                if file_name.lower().endswith('.csv'):
                    logger.info("📄 Processing CSV file")
                    df = pd.read_csv(io.BytesIO(file_content))
                elif file_name.lower().endswith(('.xlsx', '.xls')):
                    logger.info("📊 Processing Excel file")
                    df = pd.read_excel(io.BytesIO(file_content))
                else:
                    logger.error(f"❌ Unsupported file format: {file_name}")
                    raise ValueError("Unsupported file format")
                
                logger.info(f"📊 File loaded successfully - Shape: {df.shape}")
                logger.info(f"📋 Columns: {list(df.columns)}")
                
                # Validate file size (Trial V1 limit: 1000 rows)
                if len(df) > 1000:
                    logger.error(f"❌ File too large: {len(df)} rows (max: 1000)")
                    raise ValueError("File too large. Maximum 1000 rows allowed for Trial V1.")
                
                logger.info(f"✅ File size validation passed: {len(df)} rows")
                
                # Process with AI (replaces simple 'done' column)
                logger.info("🤖 Starting AI processing")
                processed_df, ai_summary = ProcessingService._process_with_ai(df, prompt)
                logger.info(f"✅ AI processing completed: {ai_summary}")
                
                # Convert back to CSV
                logger.info("💾 Converting processed data to CSV")
                output_buffer = io.BytesIO()
                processed_df.to_csv(output_buffer, index=False)
                output_buffer.seek(0)
                processed_data = output_buffer.getvalue()
                logger.info(f"✅ CSV conversion completed - Size: {len(processed_data)} bytes")
                
                # Create processing summary
                processing_summary = [
                    f"Processed {len(df)} records with AI",
                    f"User request: {prompt}",
                    f"AI processing: {ai_summary}",
                    "Ready for download"
                ]
                logger.info(f"📋 Processing summary created: {processing_summary}")
                
                # Update job status
                logger.info("📝 Updating job status to completed")
                job.status = 'completed'
                job.completed_at = datetime.utcnow()
                job.processing_summary = json.dumps(processing_summary)  # Store as JSON string
                db.commit()
                logger.info("✅ Job status updated successfully")
                
                logger.info("🎉 Data processing completed successfully!")
                return {
                    "success": True,
                    "data": processed_data,
                    "processingSummary": processing_summary,
                    "error": None
                }
                
            except Exception as e:
                logger.error(f"❌ File processing error: {str(e)}")
                # Update job status to failed
                job.status = 'failed'
                job.error_message = str(e)
                db.commit()
                logger.info("📝 Job status updated to failed")
                
                return {
                    "success": False,
                    "data": None,
                    "processingSummary": None,
                    "error": f"File processing error: {str(e)}"
                }
                
        except Exception as e:
            logger.error(f"❌ General processing error: {str(e)}")
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
        logger.info("🤖 Starting AI processing pipeline")
        
        # Debug: Check what's in settings
        logger.info(f"🔍 Debug - OPENAI_API_KEY exists: {bool(settings.OPENAI_API_KEY)}")
        logger.info(f"🔍 Debug - OPENAI_API_KEY length: {len(settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else 0}")
        logger.info(f"🔍 Debug - OPENAI_API_KEY preview: {settings.OPENAI_API_KEY[:10] + '...' if settings.OPENAI_API_KEY else 'None'}")
        
        try:
            # Initialize OpenAI client
            if not settings.OPENAI_API_KEY:
                logger.warning("⚠️ No OpenAI API key configured - using fallback")
                # Fallback: just add 'done' column if no API key
                df['done'] = 'done'
                return df, "No AI key configured - added 'done' column"
            
            logger.info("🔑 OpenAI API key found, initializing client")
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            
            # Step 1: Analyze data structure
            logger.info("📊 Step 1: Analyzing data structure")
            data_analysis = ProcessingService._analyze_data(df)
            logger.info(f"✅ Data analysis completed - Shape: {data_analysis['shape']}, Columns: {len(data_analysis['columns'])}")
            
            # Step 2: Create AI prompt with full context
            logger.info("📝 Step 2: Creating AI prompt")
            ai_prompt = ProcessingService._create_ai_prompt(data_analysis, user_prompt, df)
            logger.info(f"✅ AI prompt created - Length: {len(ai_prompt)} characters")
            
            # Step 3: Get AI response
            logger.info("🤖 Step 3: Getting AI response from OpenAI")
            ai_response = ProcessingService._get_ai_response(client, ai_prompt)
            logger.info(f"✅ AI response received - Code length: {len(ai_response.get('code', ''))} characters")
            
            # Step 4: Apply AI logic to create new columns
            logger.info("⚙️ Step 4: Applying AI-generated logic to dataframe")
            processed_df = ProcessingService._apply_ai_logic(df, ai_response, user_prompt)
            logger.info(f"✅ AI logic applied - New shape: {processed_df.shape}")
            
            return processed_df, ai_response.get('explanation', 'AI processing completed')
            
        except Exception as e:
            logger.error(f"❌ AI processing failed: {str(e)}")
            # Fallback: add 'done' column if AI fails
            df['done'] = f'AI Error: {str(e)}'
            return df, f"AI processing failed: {str(e)}"
    
    @staticmethod
    def _analyze_data(df: pd.DataFrame) -> dict:
        """Analyze CSV structure for AI context"""
        logger.info("🔍 Analyzing data structure and content")
        
        analysis = {
            "shape": df.shape,
            "columns": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "sample_data": df.head(3).to_dict('records'),
            "null_counts": df.isnull().sum().to_dict(),
            "unique_counts": df.nunique().to_dict()
        }
        
        logger.info(f"📊 Data shape: {analysis['shape']}")
        logger.info(f"📋 Columns: {analysis['columns']}")
        logger.info(f"🔢 Data types: {analysis['dtypes']}")
        logger.info(f"❓ Null counts: {analysis['null_counts']}")
        logger.info(f"🎯 Unique value counts: {analysis['unique_counts']}")
        
        return analysis
    
    @staticmethod
    def _create_ai_prompt(data_analysis: dict, user_prompt: str, df: pd.DataFrame) -> str:
        """Create prompt for AI to generate executable Python code"""
        
        # Sample data for context (first 5 rows)
        sample_data = df.head(5).to_string(index=False)
        
        # Use the optimized prompt from the prompts file
        return AIPrompts.get_data_processing_prompt(data_analysis, user_prompt, sample_data)
    
    @staticmethod
    def _get_ai_response(client, prompt: str) -> dict:
        """Get Python code from OpenAI"""
        logger.info("🌐 Sending request to OpenAI API")
        try:
            logger.info(f"🤖 Using model: gpt-3.5-turbo")
            logger.info(f"📝 Prompt length: {len(prompt)} characters")
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",  # Fast and cost-effective for Trial V1
                messages=[
                    {"role": "system", "content": AIPrompts.get_system_message()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            logger.info("✅ OpenAI API response received successfully")
            code = response.choices[0].message.content.strip()
            logger.info(f"📝 Raw AI response length: {len(code)} characters")
            
            # Clean up the code (remove markdown if any)
            if code.startswith("```python"):
                logger.info("🧹 Cleaning Python markdown from response")
                code = code.replace("```python", "").replace("```", "").strip()
            elif code.startswith("```"):
                logger.info("🧹 Cleaning generic markdown from response")
                code = code.replace("```", "").strip()
            
            logger.info(f"✅ Cleaned code length: {len(code)} characters")
            logger.info(f"📋 Code preview: {code[:100]}...")
            
            return {
                "code": code,
                "explanation": "AI generated pandas code"
            }
            
        except Exception as e:
            logger.error(f"❌ OpenAI API error: {str(e)}")
            return {
                "code": "df['ai_error'] = 'AI failed'",
                "explanation": f"AI processing error: {str(e)}"
            }
    
    @staticmethod
    def _apply_ai_logic(df: pd.DataFrame, ai_response: dict, user_prompt: str) -> pd.DataFrame:
        """Execute AI-generated Python code"""
        logger.info("⚙️ Starting AI logic application")
        result_df = df.copy()
        logger.info(f"📊 Original dataframe shape: {result_df.shape}")
        
        try:
            code = ai_response.get('code', '')
            logger.info(f"📝 AI-generated code to execute: {len(code)} characters")
            
            if not code or code.strip() == '':
                logger.warning("⚠️ No AI code generated - adding placeholder column")
                result_df['ai_processed'] = 'No code generated'
                return result_df
            
            # Execute the AI-generated code
            logger.info("🔒 Creating safe execution environment")
            import numpy as np
            exec_globals = {
                'df': result_df,
                'pd': pd,
                'np': np,
                'math': __import__('math'),
                'statistics': __import__('statistics'),
                '__builtins__': {
                    'len': len,
                    'str': str,
                    'int': int,
                    'float': float,
                    'round': round,
                    'max': max,
                    'min': min,
                    'sum': sum,
                    'abs': abs,
                    'pow': pow,
                    'divmod': divmod,
                    'complex': complex,
                    'bin': bin,
                    'hex': hex,
                    'oct': oct,
                    'chr': chr,
                    'ord': ord,
                    'range': range,
                    'enumerate': enumerate,
                    'zip': zip,
                    'filter': filter,
                    'map': map,
                    'reversed': reversed,
                    'sorted': sorted,
                    'any': any,
                    'all': all,
                    'isinstance': isinstance,
                    'issubclass': issubclass,
                    'hasattr': hasattr,
                    'getattr': getattr,
                    'setattr': setattr,
                    'delattr': delattr,
                    'property': property,
                    'super': super,
                    'object': object,
                    'type': type,
                    'bool': bool,
                    'list': list,
                    'tuple': tuple,
                    'dict': dict,
                    'set': set,
                    'frozenset': frozenset,
                    'slice': slice,
                    'memoryview': memoryview,
                    'bytearray': bytearray,
                    'bytes': bytes,
                    'open': open,
                    'print': print,
                    'input': input,
                    'format': format,
                    'vars': vars,
                    'dir': dir,
                    'help': help,
                    'hash': hash,
                    'id': id,
                    'callable': callable,
                    'compile': compile,
                    'eval': eval,
                    'exec': exec,
                    '__import__': __import__,
                }
            }
            
            logger.info("🚀 Executing AI-generated code")
            # Execute the code
            exec(code, exec_globals)
            logger.info("✅ Code execution completed successfully")
            
            # Get the modified dataframe
            result_df = exec_globals['df']
            logger.info(f"📊 New dataframe shape: {result_df.shape}")
            
            # Log what columns were added/modified
            original_cols = set(df.columns)
            new_cols = set(result_df.columns)
            added_cols = new_cols - original_cols
            if added_cols:
                logger.info(f"✨ New columns added: {list(added_cols)}")
            
        except Exception as e:
            logger.error(f"❌ Code execution failed: {str(e)}")
            # If code execution fails, add error column
            result_df['execution_error'] = f"Code error: {str(e)}"
            logger.info("⚠️ Added execution_error column due to failure")
        
        logger.info(f"✅ AI logic application completed - Final shape: {result_df.shape}")
        return result_df
 