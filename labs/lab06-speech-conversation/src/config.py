"""Configuration management for the Speech Conversation Lab.

Loads settings from environment variables, which are populated by:
  - azd env get-values (after provisioning with azd)
  - .env file (for local development)
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


def _load_env():
    """Load .env file if present (for local development)."""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)


@dataclass
class Config:
    """Application configuration."""

    # Azure Speech Service
    speech_key: str = ""
    speech_region: str = ""
    speech_endpoint: str = ""
    speech_resource_id: str = ""

    # Azure OpenAI
    openai_endpoint: str = ""
    openai_deployment: str = "gpt-4o"
    openai_api_version: str = "2024-12-01-preview"

    # Speech synthesis settings
    speech_voice: str = "en-US-JennyNeural"
    speech_language: str = "en-US"

    # Auto language detection
    auto_detect_language: bool = False
    candidate_languages: list[str] = field(
        default_factory=lambda: ["en-US", "en-GB", "hu-HU"]
    )

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        _load_env()
        return cls(
            speech_key=os.getenv("AZURE_SPEECH_KEY", ""),
            speech_region=os.getenv(
                "AZURE_SPEECH_REGION", os.getenv("AZURE_LOCATION", "eastus2")
            ),
            speech_endpoint=os.getenv("AZURE_SPEECH_ENDPOINT", ""),
            speech_resource_id=os.getenv("AZURE_SPEECH_RESOURCE_ID", ""),
            openai_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
            openai_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o"),
            openai_api_version=os.getenv(
                "AZURE_OPENAI_API_VERSION", "2024-12-01-preview"
            ),
            speech_voice=os.getenv("SPEECH_VOICE", "en-US-JennyNeural"),
            speech_language=os.getenv("SPEECH_LANGUAGE", "en-US"),
        )

    def validate(self) -> list[str]:
        """Return a list of missing required configuration values."""
        errors = []
        if not self.openai_endpoint:
            errors.append("AZURE_OPENAI_ENDPOINT is required")
        if not self.speech_key and not self.speech_endpoint:
            errors.append(
                "Either AZURE_SPEECH_KEY or AZURE_SPEECH_ENDPOINT is required"
            )
        if not self.speech_region:
            errors.append("AZURE_SPEECH_REGION is required")
        return errors
