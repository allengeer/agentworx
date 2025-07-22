"""
Unified configuration management for Sengy using pydantic-settings.
Handles environment variables, secrets, and configuration in a type-safe way.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEBUG = False

class OpenAIConfig(BaseModel):
    """OpenAI API configuration."""
    api_key: Optional[SecretStr] = Field(default=None, description="OpenAI API key")
    model: str = Field(default="openai:o3-mini", description="Default OpenAI model")
    temperature: float = Field(default=0.1, ge=0.0, le=2.0, description="Model temperature")
    max_tokens: int = Field(default=2000, gt=0, description="Maximum tokens")
    timeout: int = Field(default=30, gt=0, description="Request timeout in seconds")


class JiraConfig(BaseModel):
    """Jira API configuration."""
    username: Optional[str] = Field(default=None, description="Jira username")
    api_token: Optional[SecretStr] = Field(default=None, description="Jira API token")
    instance_url: Optional[str] = Field(default=None, description="Jira instance URL")
    cloud: bool = Field(default=True, description="Whether using Jira Cloud")


class GitHubConfig(BaseModel):
    """GitHub API configuration."""
    token: Optional[SecretStr] = Field(default=None, description="GitHub personal access token")
    api_url: str = Field(default="https://api.github.com", description="GitHub API URL")
    timeout: int = Field(default=30, gt=0, description="Request timeout in seconds")


class LangSmithConfig(BaseModel):
    """LangSmith configuration for evaluation and tracing."""
    api_key: Optional[SecretStr] = Field(default=None, description="LangSmith API key")
    project_name: str = Field(default="sengy-engineering", description="LangSmith project name")
    endpoint: str = Field(default="https://api.smith.langchain.com", description="LangSmith API endpoint")
    tracing_enabled: bool = Field(default=True, description="Enable LangSmith tracing")


class EvaluationConfig(BaseModel):
    """Evaluation framework configuration."""
    dataset_name: str = Field(default="sengy_engineering_scenarios", description="Default dataset name")
    experiment_prefix: str = Field(default="sengy_eval", description="Experiment prefix")
    max_concurrency: int = Field(default=3, gt=0, description="Max parallel evaluations")
    timeout_seconds: int = Field(default=60, gt=0, description="Evaluation timeout")
    
    # Evaluation thresholds
    engineering_relevance_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    technical_accuracy_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    actionability_threshold: float = Field(default=0.6, ge=0.0, le=1.0)


class DatabaseConfig(BaseModel):
    """Database configuration (for future use)."""
    url: Optional[str] = Field(default=None, description="Database URL")
    max_connections: int = Field(default=10, gt=0, description="Max database connections")
    timeout: int = Field(default=30, gt=0, description="Database timeout")


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = Field(default="INFO", description="Log level")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format"
    )
    file_path: Optional[str] = Field(default=None, description="Log file path")


class SengySettings(BaseSettings):
    """
    Main Sengy configuration using pydantic-settings.
    Automatically loads from environment variables and .env files.
    """
    
    model_config = SettingsConfigDict(
        env_file=[".env", Path(__file__).parent.parent / ".env"],
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application settings
    app_name: str = Field(default="Sengy", description="Application name")
    version: str = Field(default="0.1.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    environment: str = Field(default="development", description="Environment (development/production)")
    
    # API configurations
    openai: OpenAIConfig = Field(default_factory=OpenAIConfig)
    jira: JiraConfig = Field(default_factory=JiraConfig)
    github: GitHubConfig = Field(default_factory=GitHubConfig)
    langsmith: LangSmithConfig = Field(default_factory=LangSmithConfig)
    
    # Feature configurations
    evaluation: EvaluationConfig = Field(default_factory=EvaluationConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    
    # Rate limiting
    rate_limit_requests_per_second: int = Field(default=4, gt=0)
    rate_limit_burst_capacity: int = Field(default=10, gt=0)
    
    # Memory and performance
    max_message_tokens: int = Field(default=384, gt=0)
    recursion_limit: int = Field(default=50, gt=0)
    
    @field_validator("openai", mode="before")
    @classmethod
    def validate_openai_config(cls, v):
        """Validate OpenAI configuration by mapping standard env vars to nested structure."""
        if isinstance(v, dict):
            # Even when we get a dict from nested env vars, check for OPENAI_API_KEY
            if "api_key" not in v or not v["api_key"]:
                openai_key = os.getenv("OPENAI_API_KEY")
                if openai_key:
                    v["api_key"] = openai_key
            return v
        
        # Create config from standard environment variables
        config = {}
        
        # Map standard environment variables to nested structure
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            config["api_key"] = openai_key
        
        # Use double-underscore vars if available, otherwise use defaults
        config["model"] = os.getenv("OPENAI__MODEL", "openai:o3-mini")
        config["temperature"] = float(os.getenv("OPENAI__TEMPERATURE", "0.1"))
        config["max_tokens"] = int(os.getenv("OPENAI__MAX_TOKENS", "2000"))
        config["timeout"] = int(os.getenv("OPENAI__TIMEOUT", "30"))
        
        return config
    
    @field_validator("jira", mode="before")
    @classmethod
    def validate_jira_config(cls, v):
        """Validate Jira configuration by mapping standard env vars to nested structure."""
        if isinstance(v, dict):
            return v
        
        # Create config from standard environment variables
        config = {}
        
        # Map standard environment variables that Jira libraries expect
        if os.getenv("JIRA_USERNAME"):
            config["username"] = os.getenv("JIRA_USERNAME")
        if os.getenv("JIRA_API_TOKEN"):
            config["api_token"] = os.getenv("JIRA_API_TOKEN")
        if os.getenv("JIRA_INSTANCE_URL"):
            config["instance_url"] = os.getenv("JIRA_INSTANCE_URL")
        
        # Handle JIRA_CLOUD - case insensitive True/False
        jira_cloud_str = os.getenv("JIRA_CLOUD", "true")
        config["cloud"] = jira_cloud_str.lower() == "true"
        
        return config
    
    @field_validator("github", mode="before")
    @classmethod
    def validate_github_config(cls, v):
        """Validate GitHub configuration by mapping standard env vars to nested structure."""
        if isinstance(v, dict):
            # Only use GITHUB_TOKEN if token is not already set in dict
            if "token" not in v or not v["token"]:
                github_token = os.getenv("GITHUB_TOKEN")
                if github_token:
                    v["token"] = github_token
            
            # Fill in defaults for missing values
            if "api_url" not in v:
                v["api_url"] = os.getenv("GITHUB__API_URL", "https://api.github.com")
            if "timeout" not in v:
                v["timeout"] = int(os.getenv("GITHUB__TIMEOUT", "30"))
            return v
        
        # Create config from standard environment variables
        config = {}
        
        # Map standard environment variables that GitHub libraries expect
        # Prioritize GITHUB_TOKEN over GITHUB__TOKEN
        if os.getenv("GITHUB_TOKEN"):
            config["token"] = os.getenv("GITHUB_TOKEN")
        
        # Use double-underscore vars if available, otherwise use defaults
        config["api_url"] = os.getenv("GITHUB__API_URL", "https://api.github.com")
        config["timeout"] = int(os.getenv("GITHUB__TIMEOUT", "30"))
        
        return config
    
    @field_validator("langsmith", mode="before")
    @classmethod
    def validate_langsmith_config(cls, v):
        """Validate LangSmith configuration by mapping standard env vars to nested structure."""
        if isinstance(v, dict):
            # Check for standard env vars that don't use nested delimiter
            if "api_key" not in v or not v["api_key"]:
                langsmith_key = os.getenv("LANGSMITH_API_KEY")
                if langsmith_key:
                    v["api_key"] = langsmith_key
            if "project_name" not in v or not v["project_name"]:
                project = os.getenv("LANGSMITH_PROJECT")
                if project:
                    v["project_name"] = project
            if "endpoint" not in v or not v["endpoint"]:
                endpoint = os.getenv("LANGSMITH_ENDPOINT")
                if endpoint:
                    v["endpoint"] = endpoint
            if "tracing_enabled" not in v:
                tracing_str = os.getenv("LANGSMITH_TRACING", "true")
                v["tracing_enabled"] = tracing_str.lower() == "true"
            return v
        
        # Create config from standard environment variables
        config = {}
        
        # Map standard environment variables that LangSmith expects
        if os.getenv("LANGSMITH_API_KEY"):
            config["api_key"] = os.getenv("LANGSMITH_API_KEY")
        if os.getenv("LANGSMITH_PROJECT"):
            config["project_name"] = os.getenv("LANGSMITH_PROJECT")
        if os.getenv("LANGSMITH_ENDPOINT"):
            config["endpoint"] = os.getenv("LANGSMITH_ENDPOINT")
        
        # Handle LANGSMITH_TRACING boolean
        tracing_str = os.getenv("LANGSMITH_TRACING", "true")
        config["tracing_enabled"] = tracing_str.lower() == "true"
        
        return config
    
    def validate_required_secrets(self, for_evaluation: bool = False) -> List[str]:
        """
        Validate that required secrets are present.
        
        Args:
            for_evaluation: If True, also check LangSmith API key
            
        Returns:
            List of missing required secrets
        """
        missing = []
        
        # Always required
        if not self.openai.api_key:
            missing.append("OPENAI_API_KEY")
            
        # Required for Jira functionality
        if not self.jira.api_token and self.jira.instance_url:
            missing.append("JIRA_API_TOKEN")
            
        # Required for evaluation
        if for_evaluation and not self.langsmith.api_key:
            missing.append("LANGSMITH_API_KEY")
            
        return missing
    
    def get_github_token(self) -> Optional[str]:
        """Get GitHub token as string."""
        if self.github.token:
            return self.github.token.get_secret_value()
        return None
    
    def get_openai_api_key(self) -> str:
        """Get OpenAI API key as string."""
        if self.openai.api_key:
            return self.openai.api_key.get_secret_value()
        raise ValueError("OpenAI API key not configured")
    
    def get_jira_api_token(self) -> Optional[str]:
        """Get Jira API token as string."""
        if self.jira.api_token:
            return self.jira.api_token.get_secret_value()
        return None
    
    def get_langsmith_api_key(self) -> Optional[str]:
        """Get LangSmith API key as string."""
        if self.langsmith.api_key:
            return self.langsmith.api_key.get_secret_value()
        return None
    
    def setup_environment_variables(self):
        """Set up environment variables for LangChain and other libraries."""
        # Set OpenAI API key if available
        try:
            os.environ["OPENAI_API_KEY"] = self.get_openai_api_key()
        except ValueError:
            # OpenAI key not configured - will be caught by validation
            pass
        
        # Set LangSmith configuration
        if self.langsmith.api_key and self.langsmith.tracing_enabled:
            os.environ["LANGSMITH_API_KEY"] = self.get_langsmith_api_key()
            os.environ["LANGSMITH_PROJECT"] = self.langsmith.project_name
            os.environ["LANGCHAIN_ENDPOINT"] = self.langsmith.endpoint
            os.environ["LANGSMITH_TRACING"] = "true"
        
        # Set Jira configuration
        if self.jira.username:
            os.environ["JIRA_USERNAME"] = self.jira.username
        if self.jira.api_token:
            os.environ["JIRA_API_TOKEN"] = self.get_jira_api_token()
        if self.jira.instance_url:
            os.environ["JIRA_INSTANCE_URL"] = self.jira.instance_url
        os.environ["JIRA_CLOUD"] = str(self.jira.cloud).lower()
        
        # Set GitHub configuration
        if self.github.token:
            os.environ["GITHUB_TOKEN"] = self.get_github_token()
    


# Global settings instance
_settings: Optional[SengySettings] = None


def get_settings() -> SengySettings:
    """Get global settings instance (singleton pattern)."""
    global _settings
    if _settings is None:
        # Explicitly load .env file before creating settings
        from dotenv import load_dotenv
        load_dotenv()
        
        _settings = SengySettings()
        _settings.setup_environment_variables()
    return _settings


def reload_settings() -> SengySettings:
    """Reload settings from environment/files."""
    global _settings
    # Explicitly load .env file before creating settings
    from dotenv import load_dotenv
    load_dotenv()
    
    _settings = SengySettings()
    _settings.setup_environment_variables()
    return _settings


def get_llm():
    """
    Get initialized LLM instance using current settings.
    Lazy initialization to avoid import-time API key requirements.
    """
    from langchain.chat_models import init_chat_model
    settings = get_settings()
    # client = wrappers.wrap_openai(openai.OpenAI())
    return init_chat_model(settings.openai.model)


def validate_configuration(for_evaluation: bool = False) -> bool:
    """
    Validate that all required configuration is present.
    
    Args:
        for_evaluation: If True, also validate evaluation-specific config
        
    Returns:
        True if configuration is valid, False otherwise
    """
    settings = get_settings()
    missing = settings.validate_required_secrets(for_evaluation)
    
    if missing:
        print(f"❌ Missing required configuration: {', '.join(missing)}")
        print("\nPlease set the following environment variables:")
        for var in missing:
            print(f"export {var}=your_key_here")
        return False
    
    print("✅ Configuration validation passed")
    return True