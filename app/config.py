from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings"""

    # OpenAI
    openai_api_key: str = ""

    # Database
    database_url: str = "chat.db"

    # Model settings
    openai_model: str = "gpt-4o-mini"

    # Agent settings
    agent_instructions: str = "You are a helpful AI assistant."

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )


settings = Settings()
