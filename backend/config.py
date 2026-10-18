from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # PostgreSQL Configuration
    sql_host: str = "localhost"
    sql_user: str = "postgres"
    sql_password: str = ""
    sql_db_name: str = "postgres"
    sql_port: int = 5432

    # Gemini API Configuration
    gemini_api_key: str = ""

    # Embedding Service Configuration
    embedding_model: str = "gemini-embedding-2-preview"
    embedding_dimensions: int = 768

    # Extraction Service Configuration
    extraction_model: str = "gemini-2.5-flash"

    # Firebase Configuration
    firebase_project_id: str = ""
    firebase_credentials_path: str = Field(
        default="",
        validation_alias=AliasChoices(
            "GOOGLE_APPLICATION_CREDENTIALS", "FIREBASE_CREDENTIALS_PATH"
        ),
    )

    # Server Configuration
    port: int = 3000
    host: str = "0.0.0.0"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def database_url(self) -> str:
        # Returns standard psycopg connection string format for SQLAlchemy
        user = self.sql_user
        password = self.sql_password
        host = self.sql_host
        port = self.sql_port
        dbname = self.sql_db_name
        return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{dbname}"

    @property
    def conn_info(self) -> str:
        return f"host={self.sql_host} port={self.sql_port} user={self.sql_user} password={self.sql_password} dbname={self.sql_db_name}"


settings = Settings()
