import os

class Config:
    """Configuration management for Email Organizer AI."""

    @staticmethod
    def load_env():
        """Load environment variables from .env file."""
        from dotenv import load_dotenv
        load_dotenv()

    EMAIL_CATEGORIES = [
        'Primary',
        'Social',
        'Promotions',
        'Updates',
        'Forums',
    ]

# Load environment variables on module load
Config.load_env()