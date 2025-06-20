import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    # Configurações do Banco de Dados
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@db:5432/aiqfome_db"

    # URL da Fake Store API
    FAKE_STORE_API_BASE_URL: str = "https://fakestoreapi.com"

    # Configurações JWT
    JWT_SECRET_KEY: str = "your_super_secret_jwt_key_please_change_this"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # Configurações da Documentação (Opcional, None para desabilitar)
    DOCS_URL: Optional[str] = None
    REDOC_URL: Optional[str] = None

    # Google OAuth
    GOOGLE_CLIENT_ID: str = "YOUR_GOOGLE_CLIENT_ID"
    GOOGLE_CLIENT_SECRET: str = "YOUR_GOOGLE_CLIENT_SECRET"
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/auth/google/callback"
    GOOGLE_METADATA_URI: str = "https://accounts.google.com/.well-known/openid-configuration"
    SECRET_KEY_SESSION: str = "YOUR_SUPER_SECRET_SESSION_KEY"

    # Tipo de Log
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()
