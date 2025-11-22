from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Application
    app_name: str = "Queue API"
    app_env: str = "development"
    app_version: str = "1.0.0"
    debug: bool = True
    secret_key: str
    app_url: Optional[str] = None
    app_path: Optional[str] = None

    # Database
    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str
    db_password: str
    db_name: str
    database_url: Optional[str] = None

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_password: Optional[str] = None
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    
    # CORS
    allowed_origins: list = ["*"]
    allowed_methods: list = ["*"]
    allowed_headers: list = ["*"]
    
    # Logging
    log_level: str = "INFO"
    log_dir: str = "logs"
    log_file: str = "logs/app.log"

    @property
    def async_database_url(self) -> str:
        if self.database_url:
            return self.database_url.replace("mysql://", "mysql+aiomysql://")
        return f"mysql+aiomysql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
