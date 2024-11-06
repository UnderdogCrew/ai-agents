from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # API Settings
    API_TITLE: str = "Trip Planner API"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG_MODE: bool = False
    API_VERSION: str = "1.0.0"
    
    # API Keys
    OPENAI_API_KEY: str
    SERPER_API_KEY: str
    SEC_API_API_KEY: str
    BROWSERLESS_API_KEY: str
    OPENAI_MODEL_NAME: str
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings():
    return Settings() 