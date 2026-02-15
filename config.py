"""Configuration management for Email Organizer AI.

Provides centralized configuration loading from environment variables with sensible defaults.
Supports .env file loading for local development.

Configuration includes:
- OpenAI API settings (model, API key)
- Email processing limits (content length, rate limiting)
- Category and label management
"""

import os
from typing import List, Optional


class Config:
    """Configuration management for Email Organizer AI."""

    # -----------------------------------------------------------------------------
    # LLM Provider Selection
    # -----------------------------------------------------------------------------
    @property
    def LLM_PROVIDER(self) -> str:
        """Which LLM provider to use: 'openai' or 'gemini'"""
        return os.getenv('LLM_PROVIDER', 'openai').lower()

    # -----------------------------------------------------------------------------
    # Google Gemini API Configuration
    # -----------------------------------------------------------------------------
    @property
    def GOOGLE_API_KEY(self) -> Optional[str]:
        """Google Gemini API key for AI-powered email categorization."""
        return os.getenv('GOOGLE_API_KEY')

    @property
    def GEMINI_MODEL(self) -> str:
        """Google Gemini model to use."""
        return os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')

    @staticmethod
    def load_env():
        """Load environment variables from .env file if it exists."""
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            # python-dotenv not installed, skip loading .env file
            # Environment variables from system/Codespaces will still work
            pass

    # -----------------------------------------------------------------------------
    # Gmail API Configuration
    # -----------------------------------------------------------------------------
    @property
    def GMAIL_CREDENTIALS_JSON(self) -> Optional[str]:
        """Gmail API credentials as JSON string."""
        return os.getenv('GMAIL_CREDENTIALS_JSON')
    
    @property
    def GMAIL_CREDENTIALS_PATH(self) -> Optional[str]:
        """Path to Gmail credentials file (legacy support)."""
        return os.getenv('GMAIL_CREDENTIALS_PATH')

    # -----------------------------------------------------------------------------
    # OpenAI API Configuration
    # -----------------------------------------------------------------------------
    @property
    def OPENAI_API_KEY(self) -> Optional[str]:
        """OpenAI API key for AI-powered email categorization."""
        return os.getenv('OPENAI_API_KEY')
    
    @property
    def OPENAI_MODEL(self) -> str:
        """OpenAI model to use."""
        return os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    
    @property
    def OPENAI_MAX_TOKENS(self) -> int:
        """Maximum tokens for OpenAI API calls."""
        return int(os.getenv('OPENAI_MAX_TOKENS', '500'))
    
    @property
    def MAX_EMAIL_CONTENT_LENGTH(self) -> int:
        """Maximum character length for email content sent to AI model.

        Prevents context/token length errors with LLM APIs.
        Default is 8,000 – suitable for OpenAI's base models.
        Adjust via environment variable MAX_EMAIL_CONTENT_LENGTH.
        """
        return int(os.getenv('MAX_EMAIL_CONTENT_LENGTH', '8000'))
    
    @property
    def RATE_LIMIT_DELAY(self) -> float:
        """Delay between email processing operations (seconds)."""
        return float(os.getenv('RATE_LIMIT_DELAY', '0.5'))

    # -----------------------------------------------------------------------------
    # Email Category Configuration
    # -----------------------------------------------------------------------------
    @property
    def DEFAULT_CATEGORIES(self) -> List[str]:
        """Default email categories for classification."""
        categories_str = os.getenv('DEFAULT_CATEGORIES', 
                                   'Important,Work,Personal,Promotions,Social,Newsletters,Spam')
        return [cat.strip() for cat in categories_str.split(',')]

    @property
    def CUSTOM_LABELS(self) -> List[str]:
        """Custom labels to apply to emails (optional)."""
        labels_str = os.getenv('CUSTOM_LABELS', '')
        return [label.strip() for label in labels_str.split(',') if label.strip()]