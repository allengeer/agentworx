"""
Unit tests for GitHub API wrapper and related functionality.
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from sengy.node.github import GitHubAPIWrapper
from github import Github
from github.Commit import Commit
from github.PullRequest import PullRequest
from github.Repository import Repository


class TestGitHubAPIWrapper:
    """Test the GitHubAPIWrapper class."""
    
    @pytest.fixture
    def mock_github(self):
        """Create a mock GitHub instance."""
        return Mock(spec=Github)
    
    @pytest.fixture
    def mock_repo(self):
        """Create a mock repository."""
        return Mock(spec=Repository)
    
    @pytest.fixture
    def api_wrapper(self, mock_github):
        """Create GitHubAPIWrapper with mocked GitHub."""
        with patch('sengy.node.github.Github', return_value=mock_github):
            wrapper = GitHubAPIWrapper(token="test_token")
        return wrapper
    
    def test_init_with_token(self):
        """Test initialization with token."""
        with patch('sengy.node.github.Github') as mock_github_class:
            with patch('sengy.node.github.Auth.Token') as mock_auth:
                wrapper = GitHubAPIWrapper(token="test_token")
                mock_auth.assert_called_once_with("test_token")
                mock_github_class.assert_called_once()
    
    def test_init_without_token(self):
        """Test initialization without token (unauthenticated)."""
        with patch('sengy.node.github.Github') as mock_github_class:
            with patch.dict('os.environ', {}, clear=True):
                wrapper = GitHubAPIWrapper()
                # Should create unauthenticated Github instance
                mock_github_class.assert_called_once_with()
    
    def test_init_with_env_token(self):
        """Test initialization with token from environment."""
        with patch('sengy.node.github.Github') as mock_github_class:
            with patch('sengy.node.github.Auth.Token') as mock_auth:
                with patch.dict('os.environ', {'GITHUB_TOKEN': 'env_token'}):
                    wrapper = GitHubAPIWrapper()
                    mock_auth.assert_called_once_with("env_token")
    
    def test_get_repo_caching(self, api_wrapper, mock_github):
        """Test repository caching functionality."""
        mock_repo = Mock(spec=Repository)
        mock_github.get_repo.return_value = mock_repo
        api_wrapper.github = mock_github
        
        # First call should fetch from GitHub
        repo1 = api_wrapper._get_repo("owner/repo")
        mock_github.get_repo.assert_called_once_with("owner/repo")
        
        # Second call should use cache
        repo2 = api_wrapper._get_repo("owner/repo")
        # get_repo should still only be called once
        assert mock_github.get_repo.call_count == 1
        assert repo1 is repo2
    
    def test_get_commits_basic(self, api_wrapper, mock_github, mock_repo):
        """Test basic commit retrieval."""
        # Setup mock commit
        mock_commit = Mock(spec=Commit)
        mock_commit.sha = "abc123"
        mock_commit.commit.message = "Test commit"
        mock_commit.commit.author.name = "Test Author"
        mock_commit.commit.author.email = "test@example.com"
        mock_commit.commit.author.date = datetime(2024, 1, 15, 10, 30)
        mock_commit.commit.committer.name = "Test Committer"
        mock_commit.commit.committer.email = "committer@example.com"
        mock_commit.author.login = "testuser"
        mock_commit.committer.login = "testcommitter"
        mock_commit.html_url = "https://github.com/owner/repo/commit/abc123"
        mock_commit.stats.additions = 10
        mock_commit.stats.deletions = 5
        mock_commit.stats.total = 15
        
        mock_repo.get_commits.return_value = [mock_commit]
        mock_github.get_repo.return_value = mock_repo
        api_wrapper.github = mock_github
        
        commits = api_wrapper.get_commits("owner/repo", limit=1)
        
        assert len(commits) == 1
        commit_data = commits[0]
        assert commit_data["sha"] == "abc123"
        assert commit_data["message"] == "Test commit"
        assert commit_data["author"]["name"] == "Test Author"
        assert commit_data["author"]["email"] == "test@example.com"
        assert commit_data["author"]["login"] == "testuser"
        assert commit_data["stats"]["additions"] == 10
        assert commit_data["stats"]["deletions"] == 5
        assert commit_data["stats"]["total"] == 15
    
    def test_get_commits_with_filters(self, api_wrapper, mock_github, mock_repo):
        """Test commit retrieval with date and author filters."""
        mock_repo.get_commits.return_value = []
        mock_github.get_repo.return_value = mock_repo
        api_wrapper.github = mock_github
        
        api_wrapper.get_commits(
            "owner/repo",
            since="2024-01-01T00:00:00Z",
            until="2024-01-31T23:59:59Z",
            author="testuser",
            path="src/",
            limit=10
        )
        
        # Verify get_commits was called with proper parameters
        mock_repo.get_commits.assert_called_once()
        call_args = mock_repo.get_commits.call_args[1]
        
        assert call_args["author"] == "testuser"
        assert call_args["path"] == "src/"
        assert call_args["since"] is not None
        assert call_args["until"] is not None
    
    def test_get_pull_requests_basic(self, api_wrapper, mock_github, mock_repo):
        """Test basic pull request retrieval."""
        # Setup mock PR
        mock_pr = Mock(spec=PullRequest)
        mock_pr.number = 42
        mock_pr.title = "Test PR"
        mock_pr.body = "Test description"
        mock_pr.state = "open"
        mock_pr.merged = False
        mock_pr.user.name = "Test User"
        mock_pr.user.email = "test@example.com"
        mock_pr.user.login = "testuser"
        mock_pr.created_at = datetime(2024, 1, 15, 9, 0)
        mock_pr.updated_at = datetime(2024, 1, 16, 15, 30)
        mock_pr.merged_at = None
        mock_pr.closed_at = None
        mock_pr.html_url = "https://github.com/owner/repo/pull/42"
        mock_pr.head.sha = "def456"
        mock_pr.base.sha = "abc123"
        mock_pr.head.ref = "feature-branch"
        mock_pr.base.ref = "main"
        mock_pr.changed_files = 3
        mock_pr.additions = 50
        mock_pr.deletions = 10
        mock_pr.labels = []
        mock_pr.assignees = []
        mock_pr.requested_reviewers = []
        
        mock_repo.get_pulls.return_value = [mock_pr]
        mock_github.get_repo.return_value = mock_repo
        api_wrapper.github = mock_github
        
        prs = api_wrapper.get_pull_requests("owner/repo", limit=1)
        
        assert len(prs) == 1
        pr_data = prs[0]
        assert pr_data["number"] == 42
        assert pr_data["title"] == "Test PR"
        assert pr_data["state"] == "open"
        assert pr_data["merged"] == False
        assert pr_data["author"]["login"] == "testuser"
        assert pr_data["changed_files"] == 3
        assert pr_data["additions"] == 50
        assert pr_data["deletions"] == 10
    
    def test_get_commit_details(self, api_wrapper, mock_github, mock_repo):
        """Test detailed commit retrieval."""
        # Setup mock commit with file details
        mock_commit = Mock(spec=Commit)
        mock_commit.sha = "abc123"
        mock_commit.commit.message = "Detailed commit"
        mock_commit.commit.author.name = "Test Author"
        mock_commit.commit.author.email = "test@example.com"
        mock_commit.commit.author.date = datetime(2024, 1, 15, 12, 0)
        mock_commit.commit.committer.name = "Test Committer"
        mock_commit.commit.committer.email = "committer@example.com"
        mock_commit.author.login = "testuser"
        mock_commit.committer.login = "testcommitter"
        mock_commit.html_url = "https://github.com/owner/repo/commit/abc123"
        mock_commit.stats.additions = 100
        mock_commit.stats.deletions = 20
        mock_commit.stats.total = 120
        
        # Mock file changes
        mock_file = Mock()
        mock_file.filename = "src/test.py"
        mock_file.status = "modified"
        mock_file.additions = 50
        mock_file.deletions = 10
        mock_file.changes = 60
        mock_file.patch = "@@ -1,3 +1,3 @@\n test"
        mock_commit.files = [mock_file]
        
        mock_repo.get_commit.return_value = mock_commit
        mock_github.get_repo.return_value = mock_repo
        api_wrapper.github = mock_github
        
        commit_data = api_wrapper.get_commit_details("owner/repo", "abc123")
        
        assert commit_data["sha"] == "abc123"
        assert len(commit_data["files"]) == 1
        file_data = commit_data["files"][0]
        assert file_data["filename"] == "src/test.py"
        assert file_data["status"] == "modified"
        assert file_data["additions"] == 50
        assert file_data["deletions"] == 10
        assert file_data["patch"] is not None
    
    def test_get_pr_details_with_commits_and_reviews(self, api_wrapper, mock_github, mock_repo):
        """Test detailed PR retrieval with commits and reviews."""
        # Setup mock PR
        mock_pr = Mock(spec=PullRequest)
        mock_pr.number = 42
        mock_pr.title = "Detailed PR"
        mock_pr.body = "Detailed description"
        mock_pr.state = "merged"
        mock_pr.merged = True
        mock_pr.user.name = "Test User"
        mock_pr.user.email = "test@example.com"
        mock_pr.user.login = "testuser"
        mock_pr.created_at = datetime(2024, 1, 15, 8, 0)
        mock_pr.updated_at = datetime(2024, 1, 18, 17, 0)
        mock_pr.merged_at = datetime(2024, 1, 18, 17, 30)
        mock_pr.closed_at = datetime(2024, 1, 18, 17, 30)
        mock_pr.html_url = "https://github.com/owner/repo/pull/42"
        mock_pr.head.sha = "def456"
        mock_pr.base.sha = "abc123"
        mock_pr.head.ref = "feature"
        mock_pr.base.ref = "main"
        mock_pr.changed_files = 5
        mock_pr.additions = 200
        mock_pr.deletions = 50
        mock_pr.labels = []
        mock_pr.assignees = []
        mock_pr.requested_reviewers = []
        
        # Mock commits
        mock_commit = Mock()
        mock_commit.sha = "commit123"
        mock_commit.commit.message = "PR commit"
        mock_commit.commit.author.name = "Test Author"
        mock_commit.commit.author.email = "test@example.com"
        mock_commit.commit.author.date = datetime(2024, 1, 16, 10, 0)
        mock_commit.commit.committer.name = "Test Committer"
        mock_commit.commit.committer.email = "committer@example.com"
        mock_commit.author.login = "testuser"
        mock_commit.committer.login = "testcommitter"
        mock_commit.html_url = "https://github.com/owner/repo/commit/commit123"
        mock_commit.stats.additions = 30
        mock_commit.stats.deletions = 5
        mock_commit.stats.total = 35
        mock_pr.get_commits.return_value = [mock_commit]
        
        # Mock reviews
        mock_review = Mock()
        mock_review.id = 123
        mock_review.user.login = "reviewer"
        mock_review.state = "APPROVED"
        mock_review.body = "Looks good!"
        mock_review.submitted_at = datetime(2024, 1, 17, 14, 0)
        mock_pr.get_reviews.return_value = [mock_review]
        
        mock_repo.get_pull.return_value = mock_pr
        mock_github.get_repo.return_value = mock_repo
        api_wrapper.github = mock_github
        
        pr_data = api_wrapper.get_pr_details("owner/repo", 42)
        
        assert pr_data["number"] == 42
        assert pr_data["state"] == "merged"
        assert pr_data["merged"] == True
        assert len(pr_data["commits"]) == 1
        assert pr_data["commits"][0]["sha"] == "commit123"
        assert len(pr_data["reviews"]) == 1
        assert pr_data["reviews"][0]["user"] == "reviewer"
        assert pr_data["reviews"][0]["state"] == "APPROVED"
    
    def test_commit_to_dict_conversion(self, api_wrapper):
        """Test _commit_to_dict method."""
        mock_commit = Mock(spec=Commit)
        mock_commit.sha = "abc123"
        mock_commit.commit.message = "Test commit"
        mock_commit.commit.author.name = "Test Author"
        mock_commit.commit.author.email = "test@example.com"
        mock_commit.commit.author.date = datetime(2024, 1, 15, 10, 30)
        mock_commit.commit.committer.name = "Test Committer"
        mock_commit.commit.committer.email = "committer@example.com"
        mock_commit.author.login = "testuser"
        mock_commit.committer.login = "testcommitter"
        mock_commit.html_url = "https://github.com/owner/repo/commit/abc123"
        mock_commit.stats.additions = 10
        mock_commit.stats.deletions = 5
        mock_commit.stats.total = 15
        
        commit_data = api_wrapper._commit_to_dict(mock_commit)
        
        assert commit_data["sha"] == "abc123"
        assert commit_data["message"] == "Test commit"
        assert commit_data["author"]["name"] == "Test Author"
        assert commit_data["committer"]["login"] == "testcommitter"
        assert commit_data["stats"]["total"] == 15
        assert "files" not in commit_data  # files not included by default
    
    def test_pr_to_dict_conversion(self, api_wrapper):
        """Test _pr_to_dict method."""
        mock_pr = Mock(spec=PullRequest)
        mock_pr.number = 42
        mock_pr.title = "Test PR"
        mock_pr.body = "Test description"
        mock_pr.state = "open"
        mock_pr.merged = False
        mock_pr.user.name = "Test User"
        mock_pr.user.email = "test@example.com"
        mock_pr.user.login = "testuser"
        mock_pr.created_at = datetime(2024, 1, 15, 9, 0)
        mock_pr.updated_at = datetime(2024, 1, 16, 15, 30)
        mock_pr.merged_at = None
        mock_pr.closed_at = None
        mock_pr.html_url = "https://github.com/owner/repo/pull/42"
        mock_pr.head.sha = "def456"
        mock_pr.base.sha = "abc123"
        mock_pr.head.ref = "feature"
        mock_pr.base.ref = "main"
        mock_pr.changed_files = 3
        mock_pr.additions = 50
        mock_pr.deletions = 10
        mock_pr.labels = []
        mock_pr.assignees = []
        mock_pr.requested_reviewers = []
        
        pr_data = api_wrapper._pr_to_dict(mock_pr)
        
        assert pr_data["number"] == 42
        assert pr_data["title"] == "Test PR"
        assert pr_data["state"] == "open"
        assert pr_data["merged"] == False
        assert pr_data["author"]["login"] == "testuser"
        assert pr_data["head_ref"] == "feature"
        assert pr_data["base_ref"] == "main"
        assert "commits" not in pr_data  # commits not included by default
        assert "reviews" not in pr_data  # reviews not included by default