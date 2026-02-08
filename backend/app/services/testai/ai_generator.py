from openai import AzureOpenAI
from typing import List
import os
from .parsers import parse_tests

class AITestGenerator:
    def __init__(self, api_key: str = None):
        # Use Azure implementation
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4")
    
    def generate_questions(self, topic: str, count: int = 5) -> List[dict]:
        prompt = f"""
        {topic} mavzusida {count} ta test savoli yarating.
        Har bir savol 4 ta variantga ega bo'lsin.
        To'g'ri javobni belgilang.
        Format:
        1. Savol matni?
        A) Variant 1
        B) Variant 2
        C) Variant 3
        D) Variant 4
        Javob: [A-D]
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": "Siz test savollari generatsiya qiluvchi yordamchisiz."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            content = response.choices[0].message.content
            return self.parse_ai_response(content)
        except Exception as e:
            print(f"AI Generation Error: {e}")
            raise e
    
    def parse_ai_response(self, text: str) -> List[dict]:
        """Parse AI response using existing parser logic"""
        return parse_tests(text)
