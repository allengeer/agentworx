"""
Unit tests for GitHub document conversion utilities.
"""
import pytest
from langchain.docstore.document import Document

from sengy.node.github import (
    github_commit_to_document,
    github_pr_to_document,
    github_data_to_document
)


class TestGitHubDocumentConversion:
    """Test GitHub data to Document conversion utilities."""
    
    @pytest.fixture
    def sample_commit_data(self):
        """Sample commit data for testing."""
        return {
            "sha": "abc123456789",
            "message": "Add new feature implementation\n\nThis commit adds a comprehensive new feature with proper error handling and tests.",
            "author": {
                "name": "John Developer",
                "email": "john@example.com",
                "login": "johndev"
            },
            "committer": {
                "name": "GitHub",
                "email": "noreply@github.com",
                "login": "web-flow"
            },
            "date": "2024-01-15T10:30:00Z",
            "url": "https://github.com/owner/repo/commit/abc123456789",
            "stats": {
                "additions": 150,
                "deletions": 30,
                "total": 180
            },
            "files": [
                {
                    "filename": "src/feature.py",
                    "status": "added",
                    "additions": 100,
                    "deletions": 0,
                    "changes": 100
                },
                {
                    "filename": "tests/test_feature.py",
                    "status": "added",
                    "additions": 45,
                    "deletions": 0,
                    "changes": 45
                },
                {
                    "filename": "docs/api.md",
                    "status": "modified",
                    "additions": 5,
                    "deletions": 30,
                    "changes": 35
                }
            ]
        }
    
    @pytest.fixture
    def sample_pr_data(self):
        """Sample PR data for testing."""
        return {
            "number": 42,
            "title": "Feature: Add comprehensive new functionality",
            "body": "This PR introduces a new feature that includes:\n- Core functionality implementation\n- Comprehensive test coverage\n- Updated documentation\n\nCloses #123",
            "state": "merged",
            "merged": True,
            "author": {
                "name": "Jane Developer",
                "email": "jane@example.com",
                "login": "janedev"
            },
            "created_at": "2024-01-15T09:00:00Z",
            "updated_at": "2024-01-18T16:30:00Z",
            "merged_at": "2024-01-18T16:30:00Z",
            "closed_at": "2024-01-18T16:30:00Z",
            "url": "https://github.com/owner/repo/pull/42",
            "head_sha": "def456789",
            "base_sha": "abc123456",
            "head_ref": "feature/new-functionality",
            "base_ref": "main",
            "changed_files": 8,
            "additions": 250,
            "deletions": 45,
            "labels": ["enhancement", "breaking-change"],
            "assignees": ["janedev", "reviewer1"],
            "requested_reviewers": ["senior-dev"],
            "commits": [
                {
                    "sha": "commit1",
                    "message": "Initial implementation",
                    "author": {"name": "Jane Developer"}
                },
                {
                    "sha": "commit2", 
                    "message": "Add tests and documentation",
                    "author": {"name": "Jane Developer"}
                }
            ],
            "reviews": [
                {
                    "id": 123,
                    "user": "senior-dev",
                    "state": "APPROVED",
                    "body": "Excellent work! Ship it."
                },
                {
                    "id": 124,
                    "user": "security-team",
                    "state": "APPROVED", 
                    "body": "Security review passed."
                }
            ]
        }
    
    def test_github_commit_to_document_basic(self, sample_commit_data):
        """Test basic commit to document conversion."""
        doc = github_commit_to_document(sample_commit_data)
        
        assert isinstance(doc, Document)
        
        # Check content includes key information
        content = doc.page_content
        assert "abc123456789" in content
        assert "Add new feature implementation" in content
        assert "John Developer" in content
        assert "johndev" in content
        assert "john@example.com" in content
        assert "2024-01-15T10:30:00Z" in content
        assert "+150 -30" in content
        assert "180 total" in content
        
        # Check file information is included
        assert "Files Changed (3)" in content
        assert "src/feature.py (added): +100 -0" in content
        assert "tests/test_feature.py (added): +45 -0" in content
        assert "docs/api.md (modified): +5 -30" in content
        
        # Check URL is included
        assert "https://github.com/owner/repo/commit/abc123456789" in content
        
        # Check metadata
        metadata = doc.metadata
        assert metadata["sha"] == "abc123456789"
        assert metadata["author"] == "johndev"
        assert metadata["date"] == "2024-01-15T10:30:00Z"
        assert metadata["type"] == "github_commit"
        assert metadata["additions"] == 150
        assert metadata["deletions"] == 30
    
    def test_github_commit_to_document_minimal_data(self):
        """Test commit conversion with minimal data."""
        minimal_commit = {
            "sha": "minimal123",
            "message": "Quick fix"
        }
        
        doc = github_commit_to_document(minimal_commit)
        
        assert isinstance(doc, Document)
        content = doc.page_content
        assert "minimal123" in content
        assert "Quick fix" in content
        assert "Author: Unknown" in content  # Default for missing author
        
        # Check metadata with defaults
        metadata = doc.metadata
        assert metadata["sha"] == "minimal123"
        assert metadata["author"] == "Unknown"
        assert metadata["type"] == "github_commit"
    
    def test_github_pr_to_document_basic(self, sample_pr_data):
        """Test basic PR to document conversion."""
        doc = github_pr_to_document(sample_pr_data)
        
        assert isinstance(doc, Document)
        
        # Check content includes key information
        content = doc.page_content
        assert "Pull Request #42" in content
        assert "Feature: Add comprehensive new functionality" in content
        assert "merged" in content
        assert "Jane Developer" in content
        assert "janedev" in content
        assert "2024-01-15T09:00:00Z" in content
        assert "2024-01-18T16:30:00Z" in content
        assert "feature/new-functionality → main" in content
        
        # Check description is included
        assert "This PR introduces a new feature" in content
        assert "Closes #123" in content
        
        # Check statistics
        assert "8 files, +250 -45" in content
        
        # Check labels and assignees
        assert "Labels: enhancement, breaking-change" in content
        assert "Assignees: janedev, reviewer1" in content
        
        # Check commits
        assert "Commits (2)" in content
        assert "commit1: Initial implementation" in content
        assert "commit2: Add tests and documentation" in content
        
        # Check reviews
        assert "Reviews (2)" in content
        assert "senior-dev: APPROVED" in content
        assert "security-team: APPROVED" in content
        
        # Check URL
        assert "https://github.com/owner/repo/pull/42" in content
        
        # Check metadata
        metadata = doc.metadata
        assert metadata["number"] == 42
        assert metadata["state"] == "merged"
        assert metadata["merged"] == True
        assert metadata["author"] == "janedev"
        assert metadata["type"] == "github_pr"
        assert metadata["changed_files"] == 8
        assert metadata["additions"] == 250
        assert metadata["deletions"] == 45
    
    def test_github_pr_to_document_minimal_data(self):
        """Test PR conversion with minimal data."""
        minimal_pr = {
            "number": 1,
            "title": "Simple fix",
            "state": "open",
            "author": {"login": "simple_user"}
        }
        
        doc = github_pr_to_document(minimal_pr)
        
        assert isinstance(doc, Document)
        content = doc.page_content
        assert "Pull Request #1" in content
        assert "Simple fix" in content
        assert "State: open" in content
        assert "Author: Unknown (simple_user)" in content
        
        # Check metadata with defaults
        metadata = doc.metadata
        assert metadata["number"] == 1
        assert metadata["state"] == "open"
        assert metadata["author"] == "simple_user"
        assert metadata["type"] == "github_pr"
    
    def test_github_pr_to_document_no_commits_or_reviews(self, sample_pr_data):
        """Test PR conversion without commits or reviews."""
        pr_data = sample_pr_data.copy()
        del pr_data["commits"]
        del pr_data["reviews"]
        
        doc = github_pr_to_document(pr_data)
        
        assert isinstance(doc, Document)
        content = doc.page_content
        assert "Commits" not in content
        assert "Reviews" not in content
    
    def test_github_data_to_document_single_commit(self, sample_commit_data):
        """Test github_data_to_document with single commit."""
        doc = github_data_to_document(sample_commit_data)
        
        assert isinstance(doc, Document)
        assert "abc123456789" in doc.page_content
        assert doc.metadata["type"] == "github_commit"
    
    def test_github_data_to_document_single_pr(self, sample_pr_data):
        """Test github_data_to_document with single PR."""
        doc = github_data_to_document(sample_pr_data)
        
        assert isinstance(doc, Document)
        assert "Pull Request #42" in doc.page_content
        assert doc.metadata["type"] == "github_pr"
    
    def test_github_data_to_document_list_of_commits(self, sample_commit_data):
        """Test github_data_to_document with list of commits."""
        commit_list = [
            sample_commit_data,
            {
                "sha": "def456",
                "message": "Second commit",
                "author": {"name": "Another Dev", "login": "anotherdev"}
            }
        ]
        
        docs = github_data_to_document(commit_list)
        
        assert isinstance(docs, list)
        assert len(docs) == 2
        assert all(isinstance(doc, Document) for doc in docs)
        assert "abc123456789" in docs[0].page_content
        assert "def456" in docs[1].page_content
    
    def test_github_data_to_document_list_of_prs(self, sample_pr_data):
        """Test github_data_to_document with list of PRs."""
        pr_list = [
            sample_pr_data,
            {
                "number": 43,
                "title": "Another PR",
                "state": "open",
                "author": {"login": "prauthor"}
            }
        ]
        
        docs = github_data_to_document(pr_list)
        
        assert isinstance(docs, list)
        assert len(docs) == 2
        assert all(isinstance(doc, Document) for doc in docs)
        assert "Pull Request #42" in docs[0].page_content
        assert "Pull Request #43" in docs[1].page_content
    
    def test_github_data_to_document_mixed_list(self, sample_commit_data, sample_pr_data):
        """Test github_data_to_document with mixed commit/PR list."""
        mixed_list = [sample_commit_data, sample_pr_data]
        
        docs = github_data_to_document(mixed_list)
        
        assert isinstance(docs, list)
        assert len(docs) == 2
        assert docs[0].metadata["type"] == "github_commit"
        assert docs[1].metadata["type"] == "github_pr"
    
    def test_github_data_to_document_unknown_data(self):
        """Test github_data_to_document with unknown data structure."""
        unknown_data = {"unknown": "data", "type": "mystery"}
        
        doc = github_data_to_document(unknown_data)
        
        assert isinstance(doc, Document)
        assert str(unknown_data) in doc.page_content
        assert doc.metadata["type"] == "github_data"
    
    def test_commit_document_content_structure(self, sample_commit_data):
        """Test that commit document has well-structured content."""
        doc = github_commit_to_document(sample_commit_data)
        content_lines = doc.page_content.split('\n')
        
        # Check expected content structure
        assert content_lines[0].startswith("Commit SHA:")
        assert any(line.startswith("Message:") for line in content_lines)
        assert any(line.startswith("Author:") for line in content_lines)
        assert any(line.startswith("Date:") for line in content_lines)
        assert any(line.startswith("Changes:") for line in content_lines)
        assert any(line.startswith("Files Changed") for line in content_lines)
        assert any(line.startswith("URL:") for line in content_lines)
    
    def test_pr_document_content_structure(self, sample_pr_data):
        """Test that PR document has well-structured content."""
        doc = github_pr_to_document(sample_pr_data)
        content_lines = doc.page_content.split('\n')
        
        # Check expected content structure
        assert content_lines[0].startswith("Pull Request #")
        assert any(line.startswith("Title:") for line in content_lines)
        assert any(line.startswith("State:") for line in content_lines)
        assert any(line.startswith("Author:") for line in content_lines)
        assert any(line.startswith("Created:") for line in content_lines)
        assert any(line.startswith("Merged:") for line in content_lines)
        assert any(line.startswith("Branches:") for line in content_lines)
        assert any(line.startswith("Changes:") for line in content_lines)
        assert any(line.startswith("Labels:") for line in content_lines)
        assert any(line.startswith("Commits") for line in content_lines)
        assert any(line.startswith("Reviews") for line in content_lines)
        assert any(line.startswith("URL:") for line in content_lines)