"""Configuration loader from .env file."""
import os
from typing import Optional
from dotenv import load_dotenv


class Config:
    """Application configuration."""
    
    def __init__(self):
        """Load configuration from .env file."""
        load_dotenv()
        
        self.base_url: str = os.getenv("OPENAI_BASE_URL", "http://localhost:8000/v1")
        self.api_key: str = os.getenv("OPENAI_API_KEY", "sk-xxxx")
        self.model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.proxy: Optional[str] = os.getenv("OPENAI_PROXY")
        self.system_prompt: str = os.getenv(
            "OPENAI_PROMPT",
            "You are a helpful coding assistant."
        )
        self.max_tokens: int = int(os.getenv("OPENAI_MAX_TOKENS", "4096"))
    
    def validate(self) -> bool:
        """Validate configuration."""
        if not self.api_key:
            return False
        if not self.base_url:
            return False
        return True


# Global config instance
config = Config()
