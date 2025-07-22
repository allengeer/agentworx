from typing import Dict, List

from ..config import get_settings
from ..node.analysis import analyze_content_tool
from ..node.github import GitHubAPIWrapper, PowerGitHubToolkit
from ..node.summarise import summarise_content_tool
from ..node.utils import DateTimeToolkit
from .agent import Agent


class GitHubGraph(Agent):
    """
    GitHub-specific graph agent for analyzing commits and pull requests.
    
    This agent extends the base Agent with GitHub-specific tools for:
    - Fetching commits and pull requests from GitHub repositories
    - Analyzing code changes and development patterns
    - Summarizing GitHub activity across different dimensions
    
    The agent follows the same plan-execute pattern as JiraGraph but focuses
    on GitHub data sources and software development metrics.
    """
    
    def __init__(self, llm, tools=None):
        """
        Initialize GitHubGraph agent.
        
        Args:
            llm: Language model for the agent
            tools: Additional tools to include (optional)
        """
        if tools is None:
            tools = []
        
        # Add PowerGitHubToolkit if GitHub tools not already present
        github_tool_names = {
            "get_github_commits", "get_github_pull_requests", 
            "get_github_commit_details", "get_github_pr_details"
        }
        
        if not any(tool.name in github_tool_names for tool in tools):
            settings = get_settings()
            github_token = settings.get_github_token()
            github_api = GitHubAPIWrapper(token=github_token)
            power_github_toolkit = PowerGitHubToolkit(github_api)
            tools.extend(power_github_toolkit.get_tools())
        
        # Add analysis and summarization tools if not already present
        if not any(tool.name == "analyze_content_tool" for tool in tools):
            tools.append(analyze_content_tool)
        if not any(tool.name == "summarise_content_tool" for tool in tools):
            tools.append(summarise_content_tool)
        
        # Add date/time utilities
        tools.extend(DateTimeToolkit().get_tools())
        
        super().__init__(llm, tools)
    
    def build_agent(self):
        """Build the GitHub-specific agent with enhanced capabilities"""
        super().build_agent()
        # The base Agent class handles the core plan-execute pattern
        # GitHub-specific tools are automatically available through the toolkit