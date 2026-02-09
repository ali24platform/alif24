from pydantic_settings import BaseSettings
from typing import Optional
import os
from pathlib import Path

class Settings(BaseSettings):
    # Server
    NODE_ENV: str = "development"
    PORT: int = 5000  # Docker Compose bilan mos
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", 5432))
    DB_NAME: str = os.getenv("DB_NAME", "postgres")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_DIALECT: str = "postgresql"
    
    # JWT
    JWT_SECRET: str = "f3611a8f90f3e156a3e018e52289758c0bd68e6c6e372c2cfb036f75a2ff2cfa"
    JWT_EXPIRES_IN: str = "7d"
    JWT_REFRESH_SECRET: str = "8d1be0276394ed5252926104b25a0bfb1444e15be3cfd4c0fefd51bb14a96fa2"
    JWT_REFRESH_EXPIRES_IN: str = "30d"
    JWT_ALGORITHM: str = "HS256"
    
    # OpenAI
    OPENAI_API_KEY: str = "your_openai_api_key_here"
    OPENAI_MODEL: str = "gpt-4"
    
    # Azure
    AZURE_STORAGE_CONNECTION_STRING: str = "DefaultEndpointsProtocol=https;AccountName=alifbe24;AccountKey=kNOPukOWmPce4VbxB7FSXL4SgVMml4zXkMTPdouqFhRLJwvp0Cp3rNpxFb3pkA766hfa00BBHSjR+AStteDO3Q==;EndpointSuffix=core.windows.net"
    AZURE_CONTAINER_NAME: str = "audiostories"
    AZURE_SPEECH_KEY: str = "54V9TJPS3HtXlzdnmUY0sgRv6NtugLsgFcf2s3yZlwS0Ogint3u6JQQJ99BLACYeBjFXJ3w3AAAYACOGlQP9"
    AZURE_SPEECH_REGION: str = "eastus"
    AZURE_OPENAI_KEY: str = "Ekghfq1yMBAeGkHM6kKpsfPrWP77Ab7x0NaQaS81I9I7zGDfbt8lJQQJ99BLACfhMk5XJ3w3AAABACOGUD56"
    AZURE_OPENAI_ENDPOINT: str = "https://deplo.cognitiveservices.azure.com/"
    AZURE_OPENAI_REGION: Optional[str] = None
    AZURE_OPENAI_DEPLOYMENT_NAME: str = "gpt-5-chat"
    AZURE_OPENAI_API_VERSION: str = "2025-01-01-preview"
    
    # Logging
    LOG_LEVEL: str = "info"
    
    # CORS
    CORS_ORIGINS: str = "*"
    CORS_ORIGIN: str = "*"
    
    # Rate Limiting
    RATE_LIMIT_WINDOW_MS: int = 900000
    RATE_LIMIT_MAX: int = 100
    
    ADMIN_SECRET_KEY: str = "nurali_secret_2026"

    # Notification Services
    ESKIZ_EMAIL: Optional[str] = "example@eskiz.uz"
    ESKIZ_PASSWORD: Optional[str] = "your_eskiz_password"
    TELEGRAM_BOT_TOKEN: str = "8379431489:AAH2xUGuEy0_FZV8vnN8_vyIII13VqDPryU"
    TELEGRAM_CHAT_ID: str = "234413715"
    
    # Email Settings
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    SMTP_PORT: int = 587
    SMTP_HOST: Optional[str] = "smtp.gmail.com"
    SMTP_USER: Optional[str] = "example@gmail.com"
    SMTP_PASSWORD: Optional[str] = "your_app_password"
    EMAILS_FROM_EMAIL: Optional[str] = "info@alif24.uz"
    EMAILS_FROM_NAME: Optional[str] = "Alif24 Platform"
    EMAILS_ENABLED: bool = True
    
    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48
        
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"
    
    @property
    def get_database_url(self) -> str:
        url = self.DATABASE_URL
        
        try:
            if url:
                if "supa=" in url or "sslmode=" in url:
                    from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
                    
                    parsed = urlparse(url)
                    query_dict = parse_qs(parsed.query)
                    
                    if 'supa' in query_dict:
                        del query_dict['supa']
                    
                    if 'sslmode' not in query_dict:
                         query_dict['sslmode'] = ['require']
                    
                    new_query = urlencode(query_dict, doseq=True)
                    parsed = parsed._replace(query=new_query)
                    url = urlunparse(parsed)
                    
        except Exception as e:
            print(f"⚠️ URL Parsing Warning: {e}")
            pass

        if url:
             if url.startswith("postgres://"):
                return url.replace("postgres://", "postgresql://", 1)
             return url

        dialect = "postgresql" if self.DB_DIALECT in ("postgresql", "postgres") else self.DB_DIALECT
        password_part = f":{self.DB_PASSWORD}" if self.DB_PASSWORD else ""
        return f"{dialect}://{self.DB_USER}{password_part}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def is_development(self) -> bool:
        return self.NODE_ENV == "development"
    
    @property
    def is_production(self) -> bool:
        return self.NODE_ENV == "production"
    
    @property
    def is_test(self) -> bool:
        return self.NODE_ENV == "test"

import logging

logger = logging.getLogger(__name__)

try:
    settings = Settings()
    logger.info(f"✅ Settings loaded from: {os.path.abspath('.env')}")
except Exception as e:
    logger.error(f"❌ Error loading settings: {e}")
    settings = Settings(_env_file=None)