"""Configuration management for WhatsApp automation tool."""

import os
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # API Keys
    openai_api_key: str = Field(default="", description="OpenAI API key")
    anthropic_api_key: str = Field(default="", description="Anthropic API key")
    
    # WhatsApp Configuration
    whatsapp_phone_number: str = Field(default="", description="Your WhatsApp phone number")
    chrome_profile_path: str = Field(default="", description="Path to Chrome profile directory")
    signup_my_name: str = Field(..., description="Display name used when auto-signing up")
    
    # LLM Configuration
    default_llm_provider: Literal["openai", "anthropic"] = Field(default="openai")
    openai_model: str = Field(default="gpt-4-turbo-preview")
    anthropic_model: str = Field(default="claude-3-sonnet-20240229")
    max_tokens: int = Field(default=1000)
    temperature: float = Field(default=0.7)
    
    # Automation Settings
    auto_reply_enabled: bool = Field(default=False)
    response_delay_seconds: int = Field(default=2)
    max_messages_per_hour: int = Field(default=50)
    
    # Logging
    log_level: str = Field(default="INFO")
    log_file: str = Field(default="logs/whatsapp_automation.log")
    
    def validate_api_keys(self) -> bool:
        """Validate that at least one LLM API key is provided."""
        if self.default_llm_provider == "openai":
            return bool(self.openai_api_key)
        elif self.default_llm_provider == "anthropic":
            return bool(self.anthropic_api_key)
        return False


# Global settings instance
settings = Settings() 