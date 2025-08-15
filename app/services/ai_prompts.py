"""
AI Prompts for Data Processing Service
Final bulletproof version
"""

class AIPrompts:
    
    @staticmethod
    def get_data_processing_prompt(data_analysis: dict, user_prompt: str, sample_data: str) -> str:
        """
        Bulletproof prompt with strict syntax rules
        """
        
        prompt = f"""Transform the dataframe 'df' according to the user request.

Available columns: {data_analysis['columns']}

USER REQUEST: {user_prompt}

STRICT RULES:
1. The dataframe 'df' already exists - work with it directly
2. Always assign results back to df (df = ...)
3. Use only double quotes for strings: "text"
4. NO single quotes, NO apostrophes, NO comments
5. Use df.reset_index() after groupby
6. Handle nulls with df.fillna(0) before calculations

PYTHON CODE (no comments, no explanations):"""
        
        return prompt
    
    @staticmethod
    def _detect_data_issues(data_analysis: dict) -> str:
        return "Ready"
    
    @staticmethod
    def _detect_business_context(data_analysis: dict) -> str:
        return "Transform"
    
    @staticmethod
    def _detect_processing_needs(data_analysis: dict, user_prompt: str) -> str:
        return "Process"
    
    @staticmethod
    def get_system_message() -> str:
        return "Generate pandas code. Use double quotes only. No comments. No explanations."