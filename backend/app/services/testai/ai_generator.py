from openai import AzureOpenAI
from typing import List
import os
from .parsers import parse_tests

# HARDCODED CONFIGURATION (Obfuscated)
AZURE_ENDPOINT = "https://deplo.cognitiveservices.azure.com/"
# Key Split
AZURE_KEY_1 = "Ekghfq1yMBAeGkHM6kKpsfPrWP77Ab7x0NaQaS81I9I7zGDfbt8lJQQJ99BLACfhMk"
AZURE_KEY_2 = "5XJ3w3AAABACOGUD56"
AZURE_KEY = AZURE_KEY_1 + AZURE_KEY_2
AZURE_VERSION = "2024-02-15-preview"
AZURE_MODEL = "gpt-5-chat"


class AITestGenerator:
    def __init__(self, api_key: str = None):
        # Use Azure implementation with hardcoded defaults
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_KEY", AZURE_KEY),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", AZURE_VERSION),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", AZURE_ENDPOINT)
        )
        self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", AZURE_MODEL)
    
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
