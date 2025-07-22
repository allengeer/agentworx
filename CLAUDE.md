# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Sengy is a Python-based conversational AI agent designed for Jira and GitHub analysis. It uses LangChain, LangGraph, and OpenAI's GPT-4 to create an interactive chat interface that can analyze Jira tickets, GitHub commits/PRs, and provide insights through a rich terminal UI.

## Development Environment

**Package Manager**: Poetry
**Python Version**: ^3.10
**Key Dependencies**: LangChain, LangGraph, PyGithub, Rich (terminal UI), PyNput (keyboard input)

## Commands

### Installation and Setup
```bash
poetry install
```

### Testing
```bash
poetry run pytest
```

### Running the Application
```bash
poetry run python sengy/sengy.py
```

### Code Formatting
The project uses isort with black profile for import sorting:
```bash
poetry run isort .
```

## Architecture

### Core Components

1. **Agent System** (`sengy/agent/`):
   - `agent.py`: Base Agent class implementing plan-execute pattern with LangGraph
   - `jira_graph.py`: JiraGraph extends Agent with Jira-specific tools and capabilities
   - `github_graph.py`: GitHubGraph extends Agent with GitHub-specific tools for commit/PR analysis
   - `sengy_graph.py`: Empty module for potential future graph implementations

2. **Node System** (`sengy/node/`):
   - `jira.py`: MaxJiraAPIWrapper for enhanced Jira API interactions with custom field parsing
   - `github.py`: GitHubAPIWrapper for GitHub API interactions with PyGithub integration
   - `analysis.py`: Content analysis tools using structured LLM outputs for dimensional scoring
   - `summarise.py`: Content summarization capabilities
   - `utils.py`: DateTimeToolkit providing date/time manipulation tools

3. **Main Interface** (`sengy/sengy.py`):
   - Rich-based TUI with scrollable chat interface
   - Real-time streaming of agent responses
   - Multi-chat session management
   - Keyboard shortcuts for navigation

### Key Patterns

- **LangGraph State Management**: Uses StateGraph with plan-execute workflow
- **Tool-based Architecture**: Modular tools for Jira, GitHub, analysis, and date operations
- **Streaming Interface**: Real-time response streaming with custom event handling
- **Rich TUI**: Terminal-based UI with panels, layouts, and live updates

### Configuration

- **Rate Limiting**: 4 requests/second with burst capacity of 10
- **Token Management**: Message trimming to 384 tokens max
- **Memory**: InMemorySaver for conversation persistence
- **Recursion Limit**: 50 for graph execution

## Configuration and Security

### Environment Variables

The application uses a unified configuration system that loads from environment variables:

**Required:**
- `OPENAI_API_KEY`: OpenAI API key for LLM functionality

**Optional:**
- `GITHUB_TOKEN`: GitHub personal access token for repository analysis
- `JIRA_API_TOKEN`: Jira API token for ticket analysis
- `JIRA_INSTANCE_URL`: Jira instance URL 
- `LANGSMITH_API_KEY`: LangSmith API key for evaluation and tracing

### Security Note

**IMPORTANT**: This codebase contains hardcoded API keys in several files. Before any development work:
- Remove hardcoded API keys from `sengy/sengy.py:58` and `sengy/node/analysis.py:15`
- Use environment variables for API key management
- Ensure no sensitive credentials are committed to version control

### GitHub Integration

The GitHubGraph agent provides comprehensive GitHub repository analysis:

**Features:**
- Commit history analysis with filtering by date, author, and file paths
- Pull request analysis including reviews and merge patterns
- Code change metrics and development patterns
- Integration with analysis and summarization tools

**Usage:**
```python
from sengy.agent import GitHubGraph
from sengy.config import get_llm

github_graph = GitHubGraph(get_llm())
github_graph.build_graph()

result = github_graph.graph.invoke({
    "input": "Analyze recent commits in facebook/react for code complexity",
    "shared_data": {}
})
```