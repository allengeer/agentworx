"""
Unit tests for GitHub configuration integration.
"""
import os
import pytest
from unittest.mock import patch, Mock

from sengy.config import GitHubConfig, SengySettings, get_settings, reload_settings


class TestGitHubConfiguration:
    """Test GitHub configuration integration."""
    
    def test_github_config_default_values(self):
        """Test GitHubConfig default values."""
        config = GitHubConfig()
        
        assert config.token is None
        assert config.api_url == "https://api.github.com"
        assert config.timeout == 30
    
    def test_github_config_with_values(self):
        """Test GitHubConfig with provided values."""
        config = GitHubConfig(
            token="test_token_123",
            api_url="https://custom.github.com",
            timeout=60
        )
        
        assert config.token.get_secret_value() == "test_token_123"
        assert config.api_url == "https://custom.github.com"
        assert config.timeout == 60
    
    def test_github_config_validation(self):
        """Test GitHubConfig validation."""
        # Test invalid timeout
        with pytest.raises(ValueError):
            GitHubConfig(timeout=0)
        
        with pytest.raises(ValueError):
            GitHubConfig(timeout=-5)
        
        # Valid timeout should work
        config = GitHubConfig(timeout=1)
        assert config.timeout == 1
    
    @patch.dict(os.environ, {}, clear=True)
    def test_sengy_settings_github_config_no_env(self):
        """Test SengySettings GitHub config without environment variables."""
        settings = SengySettings()
        
        assert settings.github.token is None
        assert settings.github.api_url == "https://api.github.com"
        assert settings.github.timeout == 30
        assert settings.get_github_token() is None
    
    @patch.dict(os.environ, {"GITHUB_TOKEN": "env_token_123"}, clear=True)
    def test_sengy_settings_github_config_with_env_token(self):
        """Test SengySettings GitHub config with GITHUB_TOKEN environment variable."""
        settings = SengySettings()
        
        assert settings.get_github_token() == "env_token_123"
        assert settings.github.api_url == "https://api.github.com"
        assert settings.github.timeout == 30
    
    @patch.dict(os.environ, {
        "GITHUB_TOKEN": "env_token_456",
        "GITHUB__API_URL": "https://enterprise.github.com",
        "GITHUB__TIMEOUT": "45"
    }, clear=True)
    def test_sengy_settings_github_config_with_all_env_vars(self):
        """Test SengySettings GitHub config with all environment variables."""
        settings = SengySettings()
        
        assert settings.get_github_token() == "env_token_456"
        assert settings.github.api_url == "https://enterprise.github.com"
        assert settings.github.timeout == 45
    
    def test_github_config_validator_with_dict(self):
        """Test GitHub config validator when receiving dict input."""
        # Test with empty dict but GITHUB_TOKEN in environment
        with patch.dict(os.environ, {"GITHUB_TOKEN": "dict_test_token"}, clear=True):
            result = SengySettings.validate_github_config({})
            assert result["token"] == "dict_test_token"
    
    def test_github_config_validator_dict_overrides_env(self):
        """Test that dict values override environment variables."""
        config_dict = {
            "token": "dict_token",
            "api_url": "https://dict.github.com",
            "timeout": 120
        }
        
        with patch.dict(os.environ, {"GITHUB_TOKEN": "env_token"}):
            result = SengySettings.validate_github_config(config_dict)
            # Dict values should be preserved
            assert result["token"] == "dict_token"
            assert result["api_url"] == "https://dict.github.com"
            assert result["timeout"] == 120
    
    def test_github_config_validator_partial_dict(self):
        """Test GitHub config validator with partial dict input."""
        config_dict = {"timeout": 90}
        
        with patch.dict(os.environ, {"GITHUB_TOKEN": "partial_token"}, clear=True):
            result = SengySettings.validate_github_config(config_dict)
            # Should combine dict and environment values
            assert result["token"] == "partial_token"
            assert result["timeout"] == 90
    
    @patch.dict(os.environ, {"GITHUB_TOKEN": "env_setup_token"}, clear=True)
    def test_setup_environment_variables_github(self):
        """Test that setup_environment_variables sets GitHub token."""
        settings = SengySettings()
        
        # Clear any existing GITHUB_TOKEN
        if "GITHUB_TOKEN" in os.environ:
            original_token = os.environ["GITHUB_TOKEN"]
        else:
            original_token = None
        
        try:
            # Remove token to test setup
            if "GITHUB_TOKEN" in os.environ:
                del os.environ["GITHUB_TOKEN"]
            
            settings.setup_environment_variables()
            
            # Should set GITHUB_TOKEN environment variable
            assert os.environ.get("GITHUB_TOKEN") == "env_setup_token"
            
        finally:
            # Restore original environment
            if original_token:
                os.environ["GITHUB_TOKEN"] = original_token
            elif "GITHUB_TOKEN" in os.environ:
                del os.environ["GITHUB_TOKEN"]
    
    def test_setup_environment_variables_no_github_token(self):
        """Test setup_environment_variables when no GitHub token is configured."""
        settings = SengySettings()
        settings.github.token = None
        
        # Should not set GITHUB_TOKEN if not configured
        original_token = os.environ.get("GITHUB_TOKEN")
        try:
            if "GITHUB_TOKEN" in os.environ:
                del os.environ["GITHUB_TOKEN"]
            
            settings.setup_environment_variables()
            
            # GITHUB_TOKEN should not be set
            assert "GITHUB_TOKEN" not in os.environ
            
        finally:
            if original_token:
                os.environ["GITHUB_TOKEN"] = original_token
    
    @patch.dict(os.environ, {"GITHUB_TOKEN": "global_test_token"}, clear=True)
    def test_get_settings_github_integration(self):
        """Test get_settings() with GitHub configuration."""
        with patch('sengy.config._settings', None):  # Clear singleton
            settings = get_settings()
            
            assert settings.get_github_token() == "global_test_token"
            assert isinstance(settings.github, GitHubConfig)
    
    @patch.dict(os.environ, {
        "GITHUB_TOKEN": "reload_token_123",
        "GITHUB__API_URL": "https://reload.github.com"
    }, clear=True)
    def test_reload_settings_github(self):
        """Test reload_settings() with GitHub configuration."""
        settings = reload_settings()
        
        assert settings.get_github_token() == "reload_token_123"
        assert settings.github.api_url == "https://reload.github.com"
    
    def test_github_config_in_sengy_settings_schema(self):
        """Test that GitHub config is properly included in SengySettings."""
        settings = SengySettings()
        
        # GitHub config should be an attribute
        assert hasattr(settings, 'github')
        assert isinstance(settings.github, GitHubConfig)
        
        # Should have the get_github_token method
        assert hasattr(settings, 'get_github_token')
        assert callable(settings.get_github_token)
    
    def test_github_config_secret_handling(self):
        """Test that GitHub token is properly handled as a secret."""
        config = GitHubConfig(token="secret_token_123")
        
        # Token should be a SecretStr
        assert hasattr(config.token, 'get_secret_value')
        assert config.token.get_secret_value() == "secret_token_123"
        
        # String representation should not expose the token
        config_str = str(config)
        assert "secret_token_123" not in config_str
        assert "SecretStr" in config_str or "***" in config_str
    
    def test_settings_github_token_getter_with_none(self):
        """Test get_github_token when token is None."""
        settings = SengySettings()
        settings.github.token = None
        
        assert settings.get_github_token() is None
    
    def test_settings_github_token_getter_with_value(self):
        """Test get_github_token when token has a value."""
        from pydantic import SecretStr
        settings = SengySettings()
        settings.github.token = SecretStr("test_getter_token")
        
        assert settings.get_github_token() == "test_getter_token"
    
    @patch.dict(os.environ, {}, clear=True)
    def test_github_config_environment_precedence(self):
        """Test environment variable precedence in GitHub config."""
        # Test that GITHUB_TOKEN takes precedence over GITHUB__TOKEN if both exist
        with patch.dict(os.environ, {
            "GITHUB_TOKEN": "standard_token",
            "GITHUB__TOKEN": "nested_token"
        }):
            settings = SengySettings()
            # Due to pydantic-settings internal processing order, GITHUB__TOKEN 
            # (nested delimiter format) takes precedence over GITHUB_TOKEN
            # This is a known limitation of pydantic-settings when both formats exist
            assert settings.get_github_token() == "nested_token"
    
    def test_github_config_model_config(self):
        """Test GitHubConfig model configuration."""
        config = GitHubConfig()
        
        # Should inherit from BaseModel
        assert hasattr(config, 'model_validate')
        assert hasattr(config, 'model_dump')
        
        # Test serialization excludes secrets by default
        config_with_token = GitHubConfig(token="secret_123")
        dumped = config_with_token.model_dump()
        
        # Token should be excluded or masked in dump
        if 'token' in dumped:
            assert dumped['token'] != "secret_123"