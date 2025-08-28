"""
Configuration settings for Facebook Scraper API
"""
import os
from typing import Optional

class Settings:
    """Application settings"""
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8091
    DEBUG: bool = True
    
    # Threading settings
    MAX_CONCURRENT_JOBS: int = 5
    JOB_TIMEOUT_MINUTES: int = 30
    
    # Storage settings
    RESULTS_DIR: str = "api_results"
    CLEANUP_AFTER_HOURS: int = 24
    
    # API settings
    API_VERSION: str = "v1"
    API_PREFIX: str = f"/api/{API_VERSION}"
    
    # Rate limiting
    DEFAULT_DELAY: float = 2.0
    MIN_DELAY: float = 1.0
    MAX_DELAY: float = 10.0
    
    def __init__(self):
        """Initialize settings"""
        # Create results directory if it doesn't exist
        os.makedirs(self.RESULTS_DIR, exist_ok=True)

# Global settings instance
settings = Settings()

