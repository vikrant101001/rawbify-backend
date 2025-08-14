"""
AI Prompts for Data Processing Service
Simple, focused prompts for data processing tasks
"""

class AIPrompts:
    
    @staticmethod
    def get_data_processing_prompt(data_analysis: dict, user_prompt: str, sample_data: str) -> str:
        """
        Optimized prompt for all types of data processing tasks
        """
        
        prompt = f"""
You are a Python/Pandas expert. You will receive a dataset and a user request to process/manipulate the data.

DATASET INFO:
- Rows: {data_analysis['shape'][0]}, Columns: {data_analysis['shape'][1]}
- Column names: {data_analysis['columns']}
- Data types: {data_analysis['dtypes']}
- Null counts: {data_analysis['null_counts']}

SAMPLE DATA (first 5 rows):
{sample_data}

USER REQUEST: {user_prompt}

TASK: Generate Python pandas code to process/manipulate the data according to the user's request.

CAPABILITIES:
- Data cleaning (remove duplicates, handle missing values, fix data types)
- Data transformation (filter, sort, group, aggregate, pivot)
- Column operations (add, modify, rename columns)
- Data analysis (statistics, insights, patterns)
- Data reshaping (melt, pivot, concatenate)

RULES:
1. The dataframe variable is called 'df'
2. Use only pandas and numpy operations
3. Handle missing/null values gracefully
4. Your code will be executed directly
5. Return only executable Python code, no explanations
6. Make the code efficient and readable

USER REQUEST: {user_prompt}

PYTHON CODE:"""
        
        return prompt
    
    @staticmethod
    def get_system_message() -> str:
        """
        System message for OpenAI API calls
        """
        return """You are a Python/pandas expert. Generate only executable pandas code. No explanations, no markdown, just pure Python code."""
