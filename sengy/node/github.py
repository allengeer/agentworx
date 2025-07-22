import os
from datetime import datetime
from typing import Annotated, Dict, List, Optional, Union

from github import Auth, Github
from github.Commit import Commit
from github.PullRequest import PullRequest
from github.Repository import Repository
from langchain.docstore.document import Document
from langchain.tools import BaseTool
from langchain_core.messages import ToolMessage
from langchain_core.tools import BaseToolkit, InjectedToolCallId, tool
from langgraph.types import Command


class GitHubAPIWrapper:
    """
    Wrapper for GitHub API using PyGithub.
    
    Provides structured access to GitHub repositories, commits, and pull requests
    with standardized data formats for analysis.
    """
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize GitHub API wrapper.
        
        Args:
            token: GitHub personal access token. If None, will try to get from GITHUB_TOKEN env var
        """
        if token is None:
            token = os.environ.get("GITHUB_TOKEN")
        
        if token:
            auth = Auth.Token(token)
            self.github = Github(auth=auth)
        else:
            # Use unauthenticated access (rate limited)
            self.github = Github()
        
        self._repo_cache = {}
    
    def _get_repo(self, repo_name: str) -> Repository:
        """Get repository object with caching"""
        if repo_name not in self._repo_cache:
            self._repo_cache[repo_name] = self.github.get_repo(repo_name)
        return self._repo_cache[repo_name]
    
    def get_commits(self, repo: str, since: str = None, until: str = None,
                   author: str = None, path: str = None, limit: int = 30) -> List[dict]:
        """
        Get commits from a GitHub repository.
        
        Args:
            repo: Repository name in format "owner/repo"
            since: ISO 8601 date string to start from
            until: ISO 8601 date string to end at
            author: Filter by author GitHub username
            path: Filter by file path
            limit: Maximum number of commits to return
            
        Returns:
            List of commit dictionaries
        """
        repository = self._get_repo(repo)
        
        # Convert string dates to datetime objects
        since_dt = datetime.fromisoformat(since.replace('Z', '+00:00')) if since else None
        until_dt = datetime.fromisoformat(until.replace('Z', '+00:00')) if until else None
        
        commits = repository.get_commits(
            since=since_dt,
            until=until_dt,
            author=author,
            path=path
        )
        
        commit_list = []
        for i, commit in enumerate(commits):
            if i >= limit:
                break
                
            commit_data = self._commit_to_dict(commit)
            commit_list.append(commit_data)
        
        return commit_list
    
    def get_pull_requests(self, repo: str, state: str = "all", 
                         since: str = None, limit: int = 30) -> List[dict]:
        """
        Get pull requests from a GitHub repository.
        
        Args:
            repo: Repository name in format "owner/repo"
            state: PR state filter ("open", "closed", "all")
            since: ISO 8601 date string to start from
            limit: Maximum number of PRs to return
            
        Returns:
            List of PR dictionaries
        """
        repository = self._get_repo(repo)
        
        prs = repository.get_pulls(state=state, sort="updated", direction="desc")
        
        pr_list = []
        for i, pr in enumerate(prs):
            if i >= limit:
                break
                
            # Filter by date if specified
            if since:
                since_dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
                if pr.updated_at < since_dt:
                    continue
            
            pr_data = self._pr_to_dict(pr)
            pr_list.append(pr_data)
        
        return pr_list
    
    def get_commit_details(self, repo: str, sha: str) -> dict:
        """
        Get detailed information about a specific commit.
        
        Args:
            repo: Repository name
            sha: Commit SHA hash
            
        Returns:
            Detailed commit dictionary
        """
        repository = self._get_repo(repo)
        commit = repository.get_commit(sha)
        return self._commit_to_dict(commit, include_files=True)
    
    def get_pr_details(self, repo: str, pr_number: int) -> dict:
        """
        Get detailed information about a specific pull request.
        
        Args:
            repo: Repository name
            pr_number: Pull request number
            
        Returns:
            Detailed PR dictionary
        """
        repository = self._get_repo(repo)
        pr = repository.get_pull(pr_number)
        return self._pr_to_dict(pr, include_commits=True, include_reviews=True)
    
    def _commit_to_dict(self, commit: Commit, include_files: bool = False) -> dict:
        """Convert PyGithub Commit to dictionary"""
        commit_data = {
            "sha": commit.sha,
            "message": commit.commit.message,
            "author": {
                "name": commit.commit.author.name,
                "email": commit.commit.author.email,
                "login": commit.author.login if commit.author else None
            },
            "committer": {
                "name": commit.commit.committer.name,
                "email": commit.commit.committer.email,
                "login": commit.committer.login if commit.committer else None
            },
            "date": commit.commit.author.date.isoformat(),
            "url": commit.html_url,
            "stats": {
                "additions": commit.stats.additions,
                "deletions": commit.stats.deletions,
                "total": commit.stats.total
            }
        }
        
        if include_files:
            commit_data["files"] = []
            for file in commit.files:
                file_data = {
                    "filename": file.filename,
                    "status": file.status,
                    "additions": file.additions,
                    "deletions": file.deletions,
                    "changes": file.changes,
                    "patch": file.patch if hasattr(file, 'patch') and file.patch else None
                }
                commit_data["files"].append(file_data)
        
        return commit_data
    
    def _pr_to_dict(self, pr: PullRequest, include_commits: bool = False, 
                   include_reviews: bool = False) -> dict:
        """Convert PyGithub PullRequest to dictionary"""
        pr_data = {
            "number": pr.number,
            "title": pr.title,
            "body": pr.body,
            "state": pr.state,
            "merged": pr.merged,
            "author": {
                "name": pr.user.name,
                "email": pr.user.email,
                "login": pr.user.login
            },
            "created_at": pr.created_at.isoformat(),
            "updated_at": pr.updated_at.isoformat(),
            "merged_at": pr.merged_at.isoformat() if pr.merged_at else None,
            "closed_at": pr.closed_at.isoformat() if pr.closed_at else None,
            "url": pr.html_url,
            "head_sha": pr.head.sha,
            "base_sha": pr.base.sha,
            "head_ref": pr.head.ref,
            "base_ref": pr.base.ref,
            "changed_files": pr.changed_files,
            "additions": pr.additions,
            "deletions": pr.deletions,
            "labels": [label.name for label in pr.labels],
            "assignees": [assignee.login for assignee in pr.assignees],
            "requested_reviewers": [reviewer.login for reviewer in pr.requested_reviewers]
        }
        
        if include_commits:
            pr_data["commits"] = []
            for commit in pr.get_commits():
                commit_data = self._commit_to_dict(commit)
                pr_data["commits"].append(commit_data)
        
        if include_reviews:
            pr_data["reviews"] = []
            for review in pr.get_reviews():
                review_data = {
                    "id": review.id,
                    "user": review.user.login,
                    "state": review.state,
                    "body": review.body,
                    "submitted_at": review.submitted_at.isoformat() if review.submitted_at else None
                }
                pr_data["reviews"].append(review_data)
        
        return pr_data


class PowerGitHubToolkit(BaseToolkit):
    """Advanced GitHub toolkit for agentic workflows with commits and PR analysis"""
    
    def __init__(self, api: GitHubAPIWrapper):
        self._api = api
    
    def get_tools(self) -> List[BaseTool]:
        return [
            self._create_get_commits_tool(),
            self._create_get_pull_requests_tool(),
            self._create_get_commit_details_tool(),
            self._create_get_pr_details_tool()
        ]
    
    def _create_get_commits_tool(self) -> BaseTool:
        """Create tool for fetching repository commits"""
        
        @tool(parse_docstring=True)
        def get_github_commits(repo: str, tool_call_id: Annotated[str, InjectedToolCallId],
                              since: str = None, until: str = None, author: str = None,
                              path: str = None, limit: int = 30) -> str:
            """
            Fetch commits from a GitHub repository.
            
            This tool retrieves commit data from GitHub and stores it in shared memory for analysis.
            Use this to gather commit history for code change analysis and development patterns.
            
            Args:
                repo: Repository name in format "owner/repo" (e.g., "facebook/react")
                since: ISO 8601 date string to start from (e.g., "2024-01-01T00:00:00Z")
                until: ISO 8601 date string to end at
                author: Filter commits by GitHub username
                path: Filter commits that touch specific file path
                limit: Maximum number of commits to return (default: 30)
            """
            commits = self._api.get_commits(repo, since, until, author, path, limit)
            
            key = f"github.commits.{tool_call_id}"
            return Command(
                update={
                    "shared_data": {key: commits},
                    "messages": [ToolMessage(
                        f"Retrieved {len(commits)} commits from {repo}. Memory key: {key}",
                        tool_call_id=tool_call_id
                    )]
                }
            )
        
        return get_github_commits
    
    def _create_get_pull_requests_tool(self) -> BaseTool:
        """Create tool for fetching repository pull requests"""
        
        @tool(parse_docstring=True)
        def get_github_pull_requests(repo: str, tool_call_id: Annotated[str, InjectedToolCallId],
                                    state: str = "all", since: str = None, limit: int = 30) -> str:
            """
            Fetch pull requests from a GitHub repository.
            
            This tool retrieves PR data from GitHub and stores it in shared memory for analysis.
            Use this to analyze code review patterns, PR metrics, and team collaboration.
            
            Args:
                repo: Repository name in format "owner/repo"
                state: PR state filter ("open", "closed", "all")
                since: ISO 8601 date string to start from
                limit: Maximum number of PRs to return (default: 30)
            """
            prs = self._api.get_pull_requests(repo, state, since, limit)
            
            key = f"github.prs.{tool_call_id}"
            return Command(
                update={
                    "shared_data": {key: prs},
                    "messages": [ToolMessage(
                        f"Retrieved {len(prs)} pull requests from {repo}. Memory key: {key}",
                        tool_call_id=tool_call_id
                    )]
                }
            )
        
        return get_github_pull_requests
    
    def _create_get_commit_details_tool(self) -> BaseTool:
        """Create tool for fetching detailed commit information"""
        
        @tool(parse_docstring=True)
        def get_github_commit_details(repo: str, sha: str, 
                                     tool_call_id: Annotated[str, InjectedToolCallId]) -> str:
            """
            Get detailed information about a specific GitHub commit.
            
            This tool fetches comprehensive commit data including file changes, patches, and statistics.
            
            Args:
                repo: Repository name in format "owner/repo"
                sha: Commit SHA hash (full or abbreviated)
            """
            commit = self._api.get_commit_details(repo, sha)
            
            key = f"github.commit.{tool_call_id}"
            return Command(
                update={
                    "shared_data": {key: commit},
                    "messages": [ToolMessage(
                        f"Retrieved detailed commit data for {sha} from {repo}. Memory key: {key}",
                        tool_call_id=tool_call_id
                    )]
                }
            )
        
        return get_github_commit_details
    
    def _create_get_pr_details_tool(self) -> BaseTool:
        """Create tool for fetching detailed PR information"""
        
        @tool(parse_docstring=True)
        def get_github_pr_details(repo: str, pr_number: int,
                                 tool_call_id: Annotated[str, InjectedToolCallId]) -> str:
            """
            Get detailed information about a specific GitHub pull request.
            
            This tool fetches comprehensive PR data including commits, reviews, and metadata.
            
            Args:
                repo: Repository name in format "owner/repo"
                pr_number: Pull request number
            """
            pr = self._api.get_pr_details(repo, pr_number)
            
            key = f"github.pr.{tool_call_id}"
            return Command(
                update={
                    "shared_data": {key: pr},
                    "messages": [ToolMessage(
                        f"Retrieved detailed PR data for #{pr_number} from {repo}. Memory key: {key}",
                        tool_call_id=tool_call_id
                    )]
                }
            )
        
        return get_github_pr_details


def github_commit_to_document(commit: dict) -> Document:
    """
    Convert a GitHub commit dictionary to a LangChain Document.
    
    Args:
        commit: Dictionary containing GitHub commit data
        
    Returns:
        Document: LangChain Document with commit content and metadata
    """
    content = f"Commit SHA: {commit.get('sha')}\n"
    content += f"Message: {commit.get('message', 'N/A')}\n"
    
    author = commit.get('author', {})
    content += f"Author: {author.get('name', 'Unknown')}"
    if author.get('login'):
        content += f" ({author['login']})"
    if author.get('email'):
        content += f" <{author['email']}>"
    content += "\n"
    
    content += f"Date: {commit.get('date', 'N/A')}\n"
    
    stats = commit.get('stats', {})
    if stats:
        content += f"Changes: +{stats.get('additions', 0)} -{stats.get('deletions', 0)} ({stats.get('total', 0)} total)\n"
    
    files = commit.get('files', [])
    if files:
        content += f"Files Changed ({len(files)}):\n"
        for file_info in files:
            filename = file_info.get('filename', 'unknown')
            additions = file_info.get('additions', 0)
            deletions = file_info.get('deletions', 0)
            status = file_info.get('status', 'modified')
            content += f"  - {filename} ({status}): +{additions} -{deletions}\n"
    
    if commit.get('url'):
        content += f"URL: {commit['url']}\n"
    
    metadata = {
        'sha': commit.get('sha', 'N/A'),
        'author': author.get('login', author.get('name', 'Unknown')),
        'date': commit.get('date', 'N/A'),
        'type': 'github_commit',
        'additions': stats.get('additions', 0),
        'deletions': stats.get('deletions', 0)
    }
    
    return Document(page_content=content, metadata=metadata)


def github_pr_to_document(pr: dict) -> Document:
    """
    Convert a GitHub pull request dictionary to a LangChain Document.
    
    Args:
        pr: Dictionary containing GitHub PR data
        
    Returns:
        Document: LangChain Document with PR content and metadata
    """
    content = f"Pull Request #{pr.get('number')}\n"
    content += f"Title: {pr.get('title', 'N/A')}\n"
    content += f"State: {pr.get('state', 'N/A')}"
    if pr.get('merged'):
        content += " (merged)"
    content += "\n"
    
    author = pr.get('author', {})
    content += f"Author: {author.get('name', 'Unknown')}"
    if author.get('login'):
        content += f" ({author['login']})"
    content += "\n"
    
    content += f"Created: {pr.get('created_at', 'N/A')}\n"
    if pr.get('merged_at'):
        content += f"Merged: {pr.get('merged_at')}\n"
    
    content += f"Branches: {pr.get('head_ref', 'unknown')} → {pr.get('base_ref', 'unknown')}\n"
    
    if pr.get('body'):
        content += f"Description:\n{pr.get('body')}\n"
    
    content += f"Changes: {pr.get('changed_files', 0)} files, +{pr.get('additions', 0)} -{pr.get('deletions', 0)}\n"
    
    labels = pr.get('labels', [])
    if labels:
        content += f"Labels: {', '.join(labels)}\n"
    
    assignees = pr.get('assignees', [])
    if assignees:
        content += f"Assignees: {', '.join(assignees)}\n"
    
    commits = pr.get('commits', [])
    if commits:
        content += f"Commits ({len(commits)}):\n"
        for commit in commits:
            sha = commit.get('sha', 'unknown')[:8]
            message = commit.get('message', 'No message').split('\n')[0][:80]
            content += f"  - {sha}: {message}\n"
    
    reviews = pr.get('reviews', [])
    if reviews:
        content += f"Reviews ({len(reviews)}):\n"
        for review in reviews:
            reviewer = review.get('user', 'unknown')
            state = review.get('state', 'unknown')
            content += f"  - {reviewer}: {state}\n"
    
    if pr.get('url'):
        content += f"URL: {pr['url']}\n"
    
    metadata = {
        'number': pr.get('number', 0),
        'state': pr.get('state', 'unknown'),
        'merged': pr.get('merged', False),
        'author': author.get('login', author.get('name', 'Unknown')),
        'type': 'github_pr',
        'changed_files': pr.get('changed_files', 0),
        'additions': pr.get('additions', 0),
        'deletions': pr.get('deletions', 0)
    }
    
    return Document(page_content=content, metadata=metadata)


def github_data_to_document(data: Union[dict, List[dict]]) -> Union[Document, List[Document]]:
    """
    Convert GitHub data to Document(s) based on the data type.
    
    Args:
        data: GitHub commit, PR, or list of commits/PRs
        
    Returns:
        Document or list of Documents
    """
    if isinstance(data, list):
        documents = []
        for item in data:
            if 'sha' in item and 'message' in item:
                # It's a commit
                documents.append(github_commit_to_document(item))
            elif 'number' in item and 'title' in item:
                # It's a PR
                documents.append(github_pr_to_document(item))
        return documents
    else:
        if 'sha' in data and 'message' in data:
            # It's a commit
            return github_commit_to_document(data)
        elif 'number' in data and 'title' in data:
            # It's a PR
            return github_pr_to_document(data)
        else:
            # Generic fallback
            return Document(page_content=str(data), metadata={'type': 'github_data'})