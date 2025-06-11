from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database and authentication settings
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ENVIRONMENT: str = "development"
    
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