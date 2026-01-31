import os
from typing import Optional
from .models import AppConfig
from .loader import ConfigLoader

# Global configuration instance
_app_config: Optional[AppConfig] = None

def get_app_config() -> AppConfig:
    """Get application configuration (singleton pattern)."""
    global _app_config
    if _app_config is None:
        loader = ConfigLoader()
        _app_config = loader.load_config()
    return _app_config

def reload_config() -> AppConfig:
    """Reload configuration (useful for testing)."""
    global _app_config
    _app_config = None
    return get_app_config()

app_config = get_app_config() # called for direct and easy usage/access

# Export main model
__all__ = ['AppConfig', 'get_app_config', 'reload_config', 'app_config']


""" 
USAGE:

from config import get_app_config

# Get configuration
config = get_app_config()

# Use configuration
if config.general_config.development_mode:
    print("Running in development mode")

db_connection = config.database_config.sql_connection_string
allowed_origins = config.hosting_config.allowed_origins

"""