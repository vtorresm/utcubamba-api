from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database and authentication settings
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ENVIRONMENT: str = "development"
    
    # Frontend URL (used in password reset emails)
    FRONTEND_URL: str = "http://localhost:3000"
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Email settings
    MAILTRAP_HOST: str = ""
    MAILTRAP_PORT: int = 587
    MAILTRAP_USERNAME: str = ""
    MAILTRAP_PASSWORD: str = ""
    MAIL_FROM: str = ""
    MAIL_FROM_NAME: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()