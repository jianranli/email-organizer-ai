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
        
        Token calculation is conservative to account for:
        - System messages and prompts (overhead)
        - Response tokens
        - Special characters and formatting (lower char/token ratio)
        
        Approximate safe limits for different models:
        - gpt-3.5-turbo (8k tokens): 8,000 chars (default)
        - gpt-3.5-turbo-16k: 50,000 chars
        - gpt-4 (8k tokens): 8,000 chars
        - gpt-4-turbo (128k): 100,000+ chars
        
        Default: 8,000 (safe for 8k token models with overhead)
        """
        return int(os.getenv('MAX_EMAIL_CONTENT_LENGTH', '8000'))
    
    @property
    def RATE_LIMIT_DELAY(self) -> float:
        """Delay in seconds between processing emails to avoid rate limits.
        
        Recommended values:
        - gpt-4 with 10k TPM limit: 2-5 seconds
        - gpt-3.5-turbo with higher limits: 0.5-1 second
        - No delay: 0
        
        Default: 3 seconds (conservative for gpt-4)
        """
        return float(os.getenv('RATE_LIMIT_DELAY', '3'))

    # -----------------------------------------------------------------------------
    # Email Processing Configuration
    # -----------------------------------------------------------------------------
    @property
    def MAX_EMAILS_TO_PROCESS(self) -> Optional[int]:
        """Maximum number of emails to process in one run."""
        value = os.getenv('MAX_EMAILS_TO_PROCESS')
        return int(value) if value else None
    
    @property
    def EMAIL_QUERY(self) -> str:
        """Gmail search query for fetching emails."""
        return os.getenv('EMAIL_QUERY', 'is:unread')
    
    @property
    def AUTO_ARCHIVE(self) -> bool:
        """Whether to automatically archive processed emails."""
        return os.getenv('AUTO_ARCHIVE', 'true').lower() == 'true'

    # -----------------------------------------------------------------------------
    # Application Settings
    # -----------------------------------------------------------------------------
    @property
    def LOG_LEVEL(self) -> str:
        """Logging level."""
        return os.getenv('LOG_LEVEL', 'INFO')
    
    @property
    def EMAIL_CATEGORIES(self) -> List[str]:
        """Email categories for AI classification."""
        # Try to load from environment variable first
        categories_env = os.getenv('EMAIL_CATEGORIES')
        if categories_env:
            return [cat.strip() for cat in categories_env.split(',')]
        
        # Default categories
        return [
            'Notes',
            'Github',
            'Primary',
        ]
    
    @property
    def CATEGORIES_TO_KEEP(self) -> List[str]:
        """Email categories to keep (others will be deleted).
        
        Only emails matching these categories will be labeled and saved.
        All other emails will be moved to trash.
        """
        categories_env = os.getenv('CATEGORIES_TO_KEEP')
        if categories_env:
            return [cat.strip() for cat in categories_env.split(',')]
        
        # Default: only keep Notes and Github
        return ['Notes', 'Github']
    
    @property
    def LABELS_TO_PRESERVE(self) -> List[str]:
        """Custom labels to preserve when cleaning up labels.
        
        These labels will NOT be deleted during label cleanup.
        Defaults to the same labels as CATEGORIES_TO_KEEP.
        """
        labels_env = os.getenv('LABELS_TO_PRESERVE')
        if labels_env:
            return [label.strip() for label in labels_env.split(',')]
        
        # Default: preserve the same labels we use for categorization
        return self.CATEGORIES_TO_KEEP

    # -----------------------------------------------------------------------------
    # Validation
    # -----------------------------------------------------------------------------
    def validate(self) -> None:
        """Validate required configuration."""
        errors = []
        
        if not self.GMAIL_CREDENTIALS_JSON and not self.GMAIL_CREDENTIALS_PATH:
            errors.append(
                "Gmail credentials not found. Set either:\n"
                "  - GMAIL_CREDENTIALS_JSON (recommended for Codespaces)\n"
                "  - GMAIL_CREDENTIALS_PATH (for local development)"
            )
        
        if not self.OPENAI_API_KEY:
            errors.append(
                "OPENAI_API_KEY is not set. Required for AI-powered email categorization.\n"
                "  Get your API key from: https://platform.openai.com/api-keys"
            )
        
        if errors:
            error_message = "Configuration validation failed:\n\n" + "\n\n".join(errors)
            raise ValueError(error_message)
    
    def __repr__(self) -> str:
        """String representation of configuration (without sensitive data)."""
        return (
            f"Config(\n"
            f"  GMAIL_CREDENTIALS: {'✓ Set' if self.GMAIL_CREDENTIALS_JSON or self.GMAIL_CREDENTIALS_PATH else '✗ Missing'}\n"
            f"  OPENAI_API_KEY: {'✓ Set' if self.OPENAI_API_KEY else '✗ Missing'}\n"
            f"  OPENAI_MODEL: {self.OPENAI_MODEL}\n"
            f"  EMAIL_QUERY: {self.EMAIL_QUERY}\n"
            f"  AUTO_ARCHIVE: {self.AUTO_ARCHIVE}\n"
            f"  LOG_LEVEL: {self.LOG_LEVEL}\n"
            f"  EMAIL_CATEGORIES: {len(self.EMAIL_CATEGORIES)} categories\n"
            f")"
        )

# Load environment variables on module load
Config.load_env()