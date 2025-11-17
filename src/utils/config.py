"""
Configuration utilities
"""
import os
from typing import Optional
from dotenv import load_dotenv


class Config:
    """Application configuration"""

    def __init__(self, env_file: Optional[str] = None):
        """
        Load configuration from environment

        Args:
            env_file: Path to .env file (optional)
        """
        if env_file and os.path.exists(env_file):
            load_dotenv(env_file)
        else:
            load_dotenv()  # Load from default .env

        self.firebase_credentials_path = os.getenv(
            'FIREBASE_CREDENTIALS_PATH',
            'firebase-credentials.json'
        )
        self.collection_name = os.getenv('FIRESTORE_COLLECTION', 'movies')
        self.scraper_headless = os.getenv('SCRAPER_HEADLESS', 'true').lower() == 'true'
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')

    def validate(self) -> bool:
        """
        Validate configuration

        Returns:
            True if valid, False otherwise
        """
        if not os.path.exists(self.firebase_credentials_path):
            print(f"Error: Firebase credentials not found at {self.firebase_credentials_path}")
            return False

        return True

    def __repr__(self) -> str:
        return (
            f"Config(firebase_credentials={self.firebase_credentials_path}, "
            f"collection={self.collection_name}, "
            f"headless={self.scraper_headless}, "
            f"log_level={self.log_level})"
        )
