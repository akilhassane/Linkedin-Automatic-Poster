import os
from dataclasses import dataclass
from typing import Optional, List

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # If dotenv is not available, environment variables should be set manually
    pass

@dataclass
class LinkedInConfig:
    """LinkedIn API configuration"""
    client_id: str
    client_secret: str
    redirect_uri: str
    access_token: Optional[str] = None

@dataclass
class LLMConfig:
    """LLM configuration"""
    provider: str = "ollama"  # "openai" or "ollama"
    openai_api_key: Optional[str] = None
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama2"
    max_tokens: int = 3000
    temperature: float = 0.7

@dataclass
class MCPConfig:
    """MCP Server configuration"""
    server_url: str
    api_key: Optional[str] = None

@dataclass
class WebScrapingConfig:
    """Web scraping configuration"""
    user_agent: str
    selenium_headless: bool = True
    selenium_timeout: int = 30
    max_pages_per_search: int = 10
    request_delay: float = 1.0

@dataclass
class ContentConfig:
    """Content generation configuration"""
    topic: str
    posting_schedule: str
    max_content_length: int = 3000
    enable_graphs: bool = True
    enable_slides: bool = True
    content_types: Optional[List[str]] = None

@dataclass
class DatabaseConfig:
    """Database configuration"""
    url: str

@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    file: str = "logs/linkedin_automation.log"

class Settings:
    """Main settings class"""
    
    def __init__(self):
        self.linkedin = LinkedInConfig(
            client_id=os.getenv("LINKEDIN_CLIENT_ID", ""),
            client_secret=os.getenv("LINKEDIN_CLIENT_SECRET", ""),
            redirect_uri=os.getenv("LINKEDIN_REDIRECT_URI", "http://localhost:8000/callback"),
            access_token=os.getenv("LINKEDIN_ACCESS_TOKEN")
        )
        
        self.llm = LLMConfig(
            provider=os.getenv("LLM_PROVIDER", "ollama"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            ollama_model=os.getenv("OLLAMA_MODEL", "llama2")
        )
        
        self.mcp = MCPConfig(
            server_url=os.getenv("MCP_SERVER_URL", "http://localhost:8080"),
            api_key=os.getenv("MCP_API_KEY")
        )
        
        self.web_scraping = WebScrapingConfig(
            user_agent=os.getenv("USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"),
            selenium_headless=os.getenv("SELENIUM_HEADLESS", "true").lower() == "true",
            selenium_timeout=int(os.getenv("SELENIUM_TIMEOUT", "30"))
        )
        
        self.content = ContentConfig(
            topic=os.getenv("CONTENT_TOPIC", "artificial intelligence"),
            posting_schedule=os.getenv("POSTING_SCHEDULE", "0 9 * * *"),
            max_content_length=int(os.getenv("MAX_CONTENT_LENGTH", "3000")),
            enable_graphs=os.getenv("ENABLE_GRAPHS", "true").lower() == "true",
            enable_slides=os.getenv("ENABLE_SLIDES", "true").lower() == "true",
            content_types=["article", "slide", "graph", "infographic"]
        )
        
        self.database = DatabaseConfig(
            url=os.getenv("DATABASE_URL", "sqlite:///data/content_history.db")
        )
        
        self.logging = LoggingConfig(
            level=os.getenv("LOG_LEVEL", "INFO"),
            file=os.getenv("LOG_FILE", "logs/linkedin_automation.log")
        )
    
    def validate(self) -> list:
        """Validate configuration and return list of errors"""
        errors = []
        
        if not self.linkedin.client_id:
            errors.append("LinkedIn Client ID is required")
        if not self.linkedin.client_secret:
            errors.append("LinkedIn Client Secret is required")
        if not self.content.topic:
            errors.append("Content topic is required")
        if self.llm.provider == "openai" and not self.llm.openai_api_key:
            errors.append("OpenAI API key is required when using OpenAI provider")
        
        return errors

# Global settings instance
settings = Settings()