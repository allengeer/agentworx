"""
Unit tests for GitHubGraph agent.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock

from sengy.agent.github_graph import GitHubGraph
from sengy.node.github import GitHubAPIWrapper, PowerGitHubToolkit


class TestGitHubGraph:
    """Test the GitHubGraph agent class."""
    
    @pytest.fixture
    def mock_llm(self):
        """Create a mock LLM."""
        return Mock()
    
    @pytest.fixture
    def mock_settings(self):
        """Create mock settings."""
        settings = Mock()
        settings.get_github_token.return_value = "test_token_123"
        return settings
    
    def test_github_graph_initialization_with_defaults(self, mock_llm):
        """Test GitHubGraph initialization with default settings."""
        with patch('sengy.agent.github_graph.get_settings') as mock_get_settings:
            mock_settings = Mock()
            mock_settings.get_github_token.return_value = "test_token"
            mock_get_settings.return_value = mock_settings
            
            with patch('sengy.agent.github_graph.GitHubAPIWrapper') as mock_api_wrapper:
                with patch('sengy.agent.github_graph.PowerGitHubToolkit') as mock_toolkit:
                    mock_toolkit_instance = Mock()
                    mock_toolkit_instance.get_tools.return_value = []
                    mock_toolkit.return_value = mock_toolkit_instance
                    
                    github_graph = GitHubGraph(mock_llm)
                    
                    # Verify GitHub API wrapper was created with token from settings
                    mock_api_wrapper.assert_called_once_with(token="test_token")
                    
                    # Verify toolkit was created with API wrapper
                    mock_toolkit.assert_called_once()
                    
                    # Verify tools were retrieved
                    mock_toolkit_instance.get_tools.assert_called_once()
    
    def test_github_graph_initialization_with_existing_tools(self, mock_llm):
        """Test GitHubGraph initialization when GitHub tools already exist."""
        # Create mock tools with GitHub tool names
        existing_tool = Mock()
        existing_tool.name = "get_github_commits"
        
        with patch('sengy.agent.github_graph.get_settings'):
            github_graph = GitHubGraph(mock_llm, tools=[existing_tool])
            
            # Should not create new GitHub tools since they already exist
            github_tool_names = [tool.name for tool in github_graph.tools if "github" in tool.name]
            assert "get_github_commits" in github_tool_names
    
    def test_github_graph_includes_analysis_tools(self, mock_llm):
        """Test that GitHubGraph includes analysis and summarization tools."""
        with patch('sengy.agent.github_graph.get_settings') as mock_get_settings:
            mock_settings = Mock()
            mock_settings.get_github_token.return_value = None
            mock_get_settings.return_value = mock_settings
            
            with patch('sengy.agent.github_graph.GitHubAPIWrapper'):
                with patch('sengy.agent.github_graph.PowerGitHubToolkit') as mock_toolkit:
                    mock_toolkit_instance = Mock()
                    mock_toolkit_instance.get_tools.return_value = []
                    mock_toolkit.return_value = mock_toolkit_instance
                    
                    github_graph = GitHubGraph(mock_llm)
                    
                    # Check that analysis and summarization tools are included
                    tool_names = [tool.name for tool in github_graph.tools]
                    assert "analyze_content_tool" in tool_names
                    assert "summarise_content_tool" in tool_names
    
    def test_github_graph_includes_datetime_tools(self, mock_llm):
        """Test that GitHubGraph includes datetime utility tools."""
        with patch('sengy.agent.github_graph.get_settings') as mock_get_settings:
            mock_settings = Mock()
            mock_settings.get_github_token.return_value = None
            mock_get_settings.return_value = mock_settings
            
            with patch('sengy.agent.github_graph.GitHubAPIWrapper'):
                with patch('sengy.agent.github_graph.PowerGitHubToolkit') as mock_toolkit:
                    mock_toolkit_instance = Mock()
                    mock_toolkit_instance.get_tools.return_value = []
                    mock_toolkit.return_value = mock_toolkit_instance
                    
                    github_graph = GitHubGraph(mock_llm)
                    
                    # Check that datetime tools are included
                    tool_names = [tool.name for tool in github_graph.tools]
                    datetime_tools = [
                        "get_todays_date", "get_todays_datetime", "get_current_time",
                        "is_leap_year", "delta", "add_delta"
                    ]
                    
                    for tool_name in datetime_tools:
                        assert tool_name in tool_names
    
    def test_github_graph_without_existing_analysis_tools(self, mock_llm):
        """Test GitHubGraph when analysis tools already exist."""
        # Create mock analysis tools
        analyze_tool = Mock()
        analyze_tool.name = "analyze_content_tool"
        summarise_tool = Mock()
        summarise_tool.name = "summarise_content_tool"
        
        existing_tools = [analyze_tool, summarise_tool]
        
        with patch('sengy.agent.github_graph.get_settings') as mock_get_settings:
            mock_settings = Mock()
            mock_settings.get_github_token.return_value = None
            mock_get_settings.return_value = mock_settings
            
            with patch('sengy.agent.github_graph.GitHubAPIWrapper'):
                with patch('sengy.agent.github_graph.PowerGitHubToolkit') as mock_toolkit:
                    mock_toolkit_instance = Mock()
                    mock_toolkit_instance.get_tools.return_value = []
                    mock_toolkit.return_value = mock_toolkit_instance
                    
                    github_graph = GitHubGraph(mock_llm, tools=existing_tools)
                    
                    # Should not duplicate analysis tools
                    tool_names = [tool.name for tool in github_graph.tools]
                    assert tool_names.count("analyze_content_tool") == 1
                    assert tool_names.count("summarise_content_tool") == 1
    
    def test_github_graph_build_agent(self, mock_llm):
        """Test that build_agent method works correctly."""
        with patch('sengy.agent.github_graph.get_settings') as mock_get_settings:
            mock_settings = Mock()
            mock_settings.get_github_token.return_value = None
            mock_get_settings.return_value = mock_settings
            
            with patch('sengy.agent.github_graph.GitHubAPIWrapper'):
                with patch('sengy.agent.github_graph.PowerGitHubToolkit') as mock_toolkit:
                    mock_toolkit_instance = Mock()
                    mock_toolkit_instance.get_tools.return_value = []
                    mock_toolkit.return_value = mock_toolkit_instance
                    
                    github_graph = GitHubGraph(mock_llm)
                    
                    # Mock the parent build_agent method
                    with patch.object(github_graph.__class__.__bases__[0], 'build_agent') as mock_parent_build:
                        github_graph.build_agent()
                        
                        # Verify parent build_agent was called
                        mock_parent_build.assert_called_once()
    
    def test_github_graph_tool_integration(self, mock_llm):
        """Test that GitHub tools are properly integrated."""
        with patch('sengy.agent.github_graph.get_settings') as mock_get_settings:
            mock_settings = Mock()
            mock_settings.get_github_token.return_value = "test_token"
            mock_get_settings.return_value = mock_settings
            
            # Create mock GitHub tools
            mock_commits_tool = Mock()
            mock_commits_tool.name = "get_github_commits"
            mock_prs_tool = Mock()
            mock_prs_tool.name = "get_github_pull_requests"
            
            with patch('sengy.agent.github_graph.GitHubAPIWrapper'):
                with patch('sengy.agent.github_graph.PowerGitHubToolkit') as mock_toolkit:
                    mock_toolkit_instance = Mock()
                    mock_toolkit_instance.get_tools.return_value = [mock_commits_tool, mock_prs_tool]
                    mock_toolkit.return_value = mock_toolkit_instance
                    
                    github_graph = GitHubGraph(mock_llm)
                    
                    # Verify GitHub tools are in the tool list
                    tool_names = [tool.name for tool in github_graph.tools]
                    assert "get_github_commits" in tool_names
                    assert "get_github_pull_requests" in tool_names
    
    def test_github_graph_handles_none_token(self, mock_llm):
        """Test GitHubGraph handles None token gracefully."""
        with patch('sengy.agent.github_graph.get_settings') as mock_get_settings:
            mock_settings = Mock()
            mock_settings.get_github_token.return_value = None
            mock_get_settings.return_value = mock_settings
            
            with patch('sengy.agent.github_graph.GitHubAPIWrapper') as mock_api_wrapper:
                with patch('sengy.agent.github_graph.PowerGitHubToolkit') as mock_toolkit:
                    mock_toolkit_instance = Mock()
                    mock_toolkit_instance.get_tools.return_value = []
                    mock_toolkit.return_value = mock_toolkit_instance
                    
                    github_graph = GitHubGraph(mock_llm)
                    
                    # Verify API wrapper was called with None token
                    mock_api_wrapper.assert_called_once_with(token=None)
    
    def test_github_graph_inheritance(self, mock_llm):
        """Test that GitHubGraph properly inherits from Agent."""
        with patch('sengy.agent.github_graph.get_settings') as mock_get_settings:
            mock_settings = Mock()
            mock_settings.get_github_token.return_value = None
            mock_get_settings.return_value = mock_settings
            
            with patch('sengy.agent.github_graph.GitHubAPIWrapper'):
                with patch('sengy.agent.github_graph.PowerGitHubToolkit') as mock_toolkit:
                    mock_toolkit_instance = Mock()
                    mock_toolkit_instance.get_tools.return_value = []
                    mock_toolkit.return_value = mock_toolkit_instance
                    
                    github_graph = GitHubGraph(mock_llm)
                    
                    # Should have Agent methods and attributes
                    assert hasattr(github_graph, 'build_graph')
                    assert hasattr(github_graph, 'tools')
                    assert hasattr(github_graph, 'llm')
                    assert github_graph.llm is mock_llm
    
    def test_github_graph_tool_count(self, mock_llm):
        """Test that GitHubGraph has expected number of tools."""
        with patch('sengy.agent.github_graph.get_settings') as mock_get_settings:
            mock_settings = Mock()
            mock_settings.get_github_token.return_value = "test_token"
            mock_get_settings.return_value = mock_settings
            
            # Mock GitHub toolkit to return 4 tools
            github_tools = [Mock() for _ in range(4)]
            for i, tool in enumerate(github_tools):
                tool.name = f"get_github_tool_{i}"
            
            with patch('sengy.agent.github_graph.GitHubAPIWrapper'):
                with patch('sengy.agent.github_graph.PowerGitHubToolkit') as mock_toolkit:
                    mock_toolkit_instance = Mock()
                    mock_toolkit_instance.get_tools.return_value = github_tools
                    mock_toolkit.return_value = mock_toolkit_instance
                    
                    github_graph = GitHubGraph(mock_llm)
                    
                    # Should have GitHub tools + analysis tools + datetime tools
                    # 4 GitHub + 2 analysis + 6 datetime = 12 total
                    assert len(github_graph.tools) >= 10  # At least the core tools
    
    def test_github_graph_custom_tools_integration(self, mock_llm):
        """Test GitHubGraph with custom additional tools."""
        custom_tool = Mock()
        custom_tool.name = "custom_tool"
        
        with patch('sengy.agent.github_graph.get_settings') as mock_get_settings:
            mock_settings = Mock()
            mock_settings.get_github_token.return_value = None
            mock_get_settings.return_value = mock_settings
            
            with patch('sengy.agent.github_graph.GitHubAPIWrapper'):
                with patch('sengy.agent.github_graph.PowerGitHubToolkit') as mock_toolkit:
                    mock_toolkit_instance = Mock()
                    mock_toolkit_instance.get_tools.return_value = []
                    mock_toolkit.return_value = mock_toolkit_instance
                    
                    github_graph = GitHubGraph(mock_llm, tools=[custom_tool])
                    
                    # Custom tool should be included
                    tool_names = [tool.name for tool in github_graph.tools]
                    assert "custom_tool" in tool_names
    
    @patch('sengy.agent.github_graph.get_settings')
    def test_github_graph_settings_integration(self, mock_get_settings, mock_llm):
        """Test integration with settings system."""
        mock_settings = Mock()
        mock_settings.get_github_token.return_value = "settings_token_456"
        mock_get_settings.return_value = mock_settings
        
        with patch('sengy.agent.github_graph.GitHubAPIWrapper') as mock_api_wrapper:
            with patch('sengy.agent.github_graph.PowerGitHubToolkit') as mock_toolkit:
                mock_toolkit_instance = Mock()
                mock_toolkit_instance.get_tools.return_value = []
                mock_toolkit.return_value = mock_toolkit_instance
                
                github_graph = GitHubGraph(mock_llm)
                
                # Verify settings were accessed
                mock_get_settings.assert_called_once()
                mock_settings.get_github_token.assert_called_once()
                
                # Verify API wrapper was created with token from settings
                mock_api_wrapper.assert_called_once_with(token="settings_token_456")