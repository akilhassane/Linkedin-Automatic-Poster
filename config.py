"""
Configuration management for LinkedIn automation system.
"""

import os
import json
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for the LinkedIn automation system."""
    
    def __init__(self):
        self.config_file = "config.json"
        self.load_config()
        
    def load_config(self) -> None:
        """Load configuration from JSON file and environment variables."""
        # Default configuration
        self.config = {
            "linkedin": {
                "client_id": os.getenv("LINKEDIN_CLIENT_ID", ""),
                "client_secret": os.getenv("LINKEDIN_CLIENT_SECRET", ""),
                "access_token": os.getenv("LINKEDIN_ACCESS_TOKEN", ""),
                "user_id": os.getenv("LINKEDIN_USER_ID", "")
            },
            "openai": {
                "api_key": os.getenv("OPENAI_API_KEY", ""),
                "model": "gpt-3.5-turbo",  # Free tier model
                "max_tokens": 2000,
                "temperature": 0.7
            },
            "mcp": {
                "server_url": os.getenv("MCP_SERVER_URL", "http://localhost:8080"),
                "api_key": os.getenv("MCP_API_KEY", "")
            },
            "content": {
                "topics": ["artificial intelligence", "machine learning", "technology trends"],
                "current_topic": "artificial intelligence",
                "post_frequency": 24,  # hours
                "content_types": ["article", "slide", "graph"],
                "max_sources": 5
            },
            "web_scraping": {
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "timeout": 30,
                "max_pages": 10
            },
            "logging": {
                "level": "INFO",
                "file": "linkedin_automation.log"
            }
        }
        
        # Load from file if exists
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    file_config = json.load(f)
                    self.merge_config(file_config)
            except Exception as e:
                print(f"Error loading config file: {e}")
    
    def merge_config(self, file_config: Dict[str, Any]) -> None:
        """Merge configuration from file with default config."""
        for key, value in file_config.items():
            if key in self.config and isinstance(value, dict):
                self.config[key].update(value)
            else:
                self.config[key] = value
    
    def save_config(self) -> None:
        """Save current configuration to JSON file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config file: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation."""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value using dot notation."""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        self.save_config()
    
    def validate_required_keys(self) -> bool:
        """Validate that all required configuration keys are present."""
        required_keys = [
            "linkedin.client_id",
            "linkedin.client_secret",
            "linkedin.access_token"
        ]
        
        missing_keys = []
        for key in required_keys:
            if not self.get(key):
                missing_keys.append(key)
        
        if missing_keys:
            print(f"Missing required configuration keys: {missing_keys}")
            return False
        
        return True

# Global configuration instance
config = Config()