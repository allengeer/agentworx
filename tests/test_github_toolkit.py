"""
Unit tests for PowerGitHubToolkit and related tools.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from langchain.tools import BaseTool
from langgraph.types import Command

from sengy.node.github import PowerGitHubToolkit, GitHubAPIWrapper


class TestPowerGitHubToolkit:
    """Test the PowerGitHubToolkit class."""
    
    @pytest.fixture
    def mock_api_wrapper(self):
        """Create a mock GitHubAPIWrapper."""
        return Mock(spec=GitHubAPIWrapper)
    
    @pytest.fixture
    def toolkit(self, mock_api_wrapper):
        """Create PowerGitHubToolkit with mocked API."""
        return PowerGitHubToolkit(mock_api_wrapper)
    
    def test_get_tools(self, toolkit):
        """Test that toolkit returns the correct tools."""
        tools = toolkit.get_tools()
        
        assert len(tools) == 4
        tool_names = [tool.name for tool in tools]
        
        expected_tools = [
            "get_github_commits",
            "get_github_pull_requests", 
            "get_github_commit_details",
            "get_github_pr_details"
        ]
        
        for expected_tool in expected_tools:
            assert expected_tool in tool_names
        
        # Verify all tools are BaseTool instances
        for tool in tools:
            assert isinstance(tool, BaseTool)
    
    def test_get_commits_tool_function(self, toolkit, mock_api_wrapper):
        """Test get_github_commits tool functionality."""
        # Setup mock data
        mock_commits = [
            {
                "sha": "abc123",
                "message": "Test commit",
                "author": {"name": "Test Author", "login": "testuser"},
                "date": "2024-01-15T10:30:00Z"
            }
        ]
        mock_api_wrapper.get_commits.return_value = mock_commits
        
        tools = toolkit.get_tools()
        commits_tool = next(tool for tool in tools if tool.name == "get_github_commits")
        
        # Test tool execution - it should return a Command instance
        result = commits_tool.func(
            repo="owner/repo",
            tool_call_id="test_call_123",
            since="2024-01-01T00:00:00Z",
            limit=10
        )
        
        # Verify API was called correctly
        mock_api_wrapper.get_commits.assert_called_once_with(
            "owner/repo",
            "2024-01-01T00:00:00Z",
            None,  # until
            None,  # author
            None,  # path
            10     # limit
        )
        
        # Verify Command was returned with correct data
        assert isinstance(result, Command)
        assert "shared_data" in result.update
        assert "github.commits.test_call_123" in result.update["shared_data"]
        assert result.update["shared_data"]["github.commits.test_call_123"] == mock_commits
    
    def test_get_pull_requests_tool_function(self, toolkit, mock_api_wrapper):
        """Test get_github_pull_requests tool functionality."""
        # Setup mock data
        mock_prs = [
            {
                "number": 42,
                "title": "Test PR",
                "state": "open",
                "author": {"login": "testuser"}
            }
        ]
        mock_api_wrapper.get_pull_requests.return_value = mock_prs
        
        tools = toolkit.get_tools()
        prs_tool = next(tool for tool in tools if tool.name == "get_github_pull_requests")
        
        # Test tool execution - it should return a Command instance
        result = prs_tool.func(
            repo="owner/repo",
            tool_call_id="test_call_456",
            state="all",
            limit=20
        )
        
        # Verify API was called correctly
        mock_api_wrapper.get_pull_requests.assert_called_once_with(
            "owner/repo",
            "all",    # state
            None,     # since
            20        # limit
        )
        
        # Verify Command was returned with correct data
        assert isinstance(result, Command)
        assert "shared_data" in result.update
        assert "github.prs.test_call_456" in result.update["shared_data"]
        assert result.update["shared_data"]["github.prs.test_call_456"] == mock_prs
    
    def test_get_commit_details_tool_function(self, toolkit, mock_api_wrapper):
        """Test get_github_commit_details tool functionality."""
        # Setup mock data
        mock_commit = {
            "sha": "abc123",
            "message": "Detailed commit",
            "files": [
                {"filename": "src/test.py", "status": "modified"}
            ]
        }
        mock_api_wrapper.get_commit_details.return_value = mock_commit
        
        tools = toolkit.get_tools()
        commit_details_tool = next(tool for tool in tools if tool.name == "get_github_commit_details")
        
        # Test tool execution - it should return a Command instance
        result = commit_details_tool.func(
            repo="owner/repo",
            sha="abc123",
            tool_call_id="test_call_789"
        )
        
        # Verify API was called correctly
        mock_api_wrapper.get_commit_details.assert_called_once_with("owner/repo", "abc123")
        
        # Verify Command was returned with correct data
        assert isinstance(result, Command)
        assert "shared_data" in result.update
        assert "github.commit.test_call_789" in result.update["shared_data"]
        assert result.update["shared_data"]["github.commit.test_call_789"] == mock_commit
    
    def test_get_pr_details_tool_function(self, toolkit, mock_api_wrapper):
        """Test get_github_pr_details tool functionality."""
        # Setup mock data
        mock_pr = {
            "number": 42,
            "title": "Detailed PR",
            "commits": [{"sha": "commit123"}],
            "reviews": [{"user": "reviewer", "state": "APPROVED"}]
        }
        mock_api_wrapper.get_pr_details.return_value = mock_pr
        
        tools = toolkit.get_tools()
        pr_details_tool = next(tool for tool in tools if tool.name == "get_github_pr_details")
        
        # Test tool execution - it should return a Command instance
        result = pr_details_tool.func(
            repo="owner/repo",
            pr_number=42,
            tool_call_id="test_call_999"
        )
        
        # Verify API was called correctly
        mock_api_wrapper.get_pr_details.assert_called_once_with("owner/repo", 42)
        
        # Verify Command was returned with correct data
        assert isinstance(result, Command)
        assert "shared_data" in result.update
        assert "github.pr.test_call_999" in result.update["shared_data"]
        assert result.update["shared_data"]["github.pr.test_call_999"] == mock_pr
    
    def test_tool_descriptions(self, toolkit):
        """Test that tools have proper descriptions."""
        tools = toolkit.get_tools()
        
        for tool in tools:
            assert tool.description is not None
            assert len(tool.description) > 20  # Reasonable description length
            assert "GitHub" in tool.description
    
    def test_tool_parameters(self, toolkit):
        """Test that tools have correct parameter schemas."""
        tools = toolkit.get_tools()
        
        commits_tool = next(tool for tool in tools if tool.name == "get_github_commits")
        # Check that repo parameter is required
        schema = commits_tool.args_schema.model_json_schema()
        assert "repo" in schema["properties"]
        assert "repo" in schema["required"]
        
        # Check optional parameters exist
        assert "since" in schema["properties"]
        assert "until" in schema["properties"]
        assert "author" in schema["properties"]
        assert "path" in schema["properties"]
        assert "limit" in schema["properties"]
        
        # since, until, author, path should be optional
        optional_params = {"since", "until", "author", "path"}
        for param in optional_params:
            assert param not in schema["required"]
    
    def test_memory_key_generation(self, toolkit, mock_api_wrapper):
        """Test that memory keys are generated consistently."""
        mock_api_wrapper.get_commits.return_value = []
        
        tools = toolkit.get_tools()
        commits_tool = next(tool for tool in tools if tool.name == "get_github_commits")
        
        result = commits_tool.func(
            repo="owner/repo",
            tool_call_id="unique_call_id_123"
        )
        
        # Verify Command was returned with correct memory key
        assert isinstance(result, Command)
        shared_data = result.update["shared_data"]
        
        # Memory key should include tool type and call ID
        expected_key = "github.commits.unique_call_id_123"
        assert expected_key in shared_data
    
    def test_error_handling(self, toolkit, mock_api_wrapper):
        """Test error handling in tools."""
        # Make API wrapper raise an exception
        mock_api_wrapper.get_commits.side_effect = Exception("API Error")
        
        tools = toolkit.get_tools()
        commits_tool = next(tool for tool in tools if tool.name == "get_github_commits")
        
        # Tool should let the exception propagate (to be handled by agent)
        with pytest.raises(Exception, match="API Error"):
            commits_tool.func(
                repo="owner/repo",
                tool_call_id="test_call"
            )
    
    def test_tool_argument_types(self, toolkit):
        """Test that tool arguments have correct types."""
        tools = toolkit.get_tools()
        
        commits_tool = next(tool for tool in tools if tool.name == "get_github_commits")
        schema = commits_tool.args_schema.model_json_schema()
        
        # String parameters
        string_params = ["repo", "since", "until", "author", "path"]
        for param in string_params:
            if param in schema["properties"]:
                assert schema["properties"][param]["type"] == "string"
        
        # Integer parameters
        if "limit" in schema["properties"]:
            assert schema["properties"]["limit"]["type"] == "integer"
        
        # PR details tool should have integer pr_number
        pr_tool = next(tool for tool in tools if tool.name == "get_github_pr_details")
        pr_schema = pr_tool.args_schema.model_json_schema()
        assert pr_schema["properties"]["pr_number"]["type"] == "integer"