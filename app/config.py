import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings"""

    # OpenAI
    openai_api_key: str = ""

    # Database - simple file path (not SQLAlchemy URL)
    database_url: str = "data/chat.db"

    # Model settings
    openai_model: str = "gpt-4o-mini"

    # Agent settings
    agent_instructions: str = "You are a helpful AI assistant."

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

    @property
    def database_path(self) -> str:
        """
        Get the actual database file path.

        Handles both simple paths (chat.db) and SQLAlchemy-style URLs
        (sqlite+aiosqlite:///./chat.db).
        """
        url = self.database_url

        # Strip SQLAlchemy prefix if present
        if url.startswith("sqlite"):
            # Handle sqlite:///./path or sqlite+aiosqlite:///./path
            url = url.split("///")[-1]
            if url.startswith("./"):
                url = url[2:]

        # Ensure parent directory exists
        path = Path(url)
        path.parent.mkdir(parents=True, exist_ok=True)

        return str(path)


settings = Settings()
