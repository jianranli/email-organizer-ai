import os
from typing import List, Optional

class Config:
    """Configuration management for Email Organizer AI."""

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
        return os.getenv('OPENAI_MODEL', 'gpt-4')
    
    @property
    def OPENAI_MAX_TOKENS(self) -> int:
        """Maximum tokens for OpenAI API calls."""
        return int(os.getenv('OPENAI_MAX_TOKENS', '500'))

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
            'Primary',
            'Social',
            'Promotions',
            'Updates',
            'Forums',
            'Important',
            'Work',
            'Personal'
        ]

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