"""
Unit tests for Jira utility functions.
"""
import pytest

from sengy.node.jira import ticket_to_document

from .fixtures import create_sample_ticket, sample_ticket
from .test_utils import count_ticket_fields_in_content, verify_document_structure


class TestTicketToDocument:
    """Test the ticket_to_document function."""
    
    def test_basic_ticket_conversion(self, sample_ticket):
        """Test converting a basic ticket to document."""
        doc = ticket_to_document(sample_ticket)
        
        # Verify structure
        assert verify_document_structure(doc, expected_key="TEST-123")
        
        # Check content contains key fields
        fields = count_ticket_fields_in_content(doc.page_content)
        assert fields['key'], "Document should contain key"
        assert fields['summary'], "Document should contain summary"
        assert fields['status'], "Document should contain status"
        assert fields['priority'], "Document should contain priority"
    
    def test_ticket_with_comments(self):
        """Test ticket with multiple comments."""
        ticket = create_sample_ticket(
            key="COMMENT-TEST",
            comments=[
                {"author": {"displayName": "Alice"}, "body": "First comment"},
                {"author": {"displayName": "Bob"}, "body": "Second comment"},
                {"author": {"displayName": "Charlie"}, "body": "Third comment"}
            ]
        )
        
        doc = ticket_to_document(ticket)
        
        # Check all comments are included
        assert "Alice: First comment" in doc.page_content
        assert "Bob: Second comment" in doc.page_content
        assert "Charlie: Third comment" in doc.page_content
        assert "Comments (3)" in doc.page_content
    
    def test_ticket_with_no_comments(self):
        """Test ticket without comments."""
        ticket = create_sample_ticket(
            key="NO-COMMENTS",
            comments=[]
        )
        
        doc = ticket_to_document(ticket)
        
        # Should not contain comments section
        assert "Comments" not in doc.page_content
    
    def test_ticket_with_labels_and_components(self):
        """Test ticket with labels and components."""
        ticket = create_sample_ticket(
            key="LABELS-TEST",
            labels=["urgent", "bug", "backend"],
            components=["Authentication", "Database", "API"]
        )
        
        doc = ticket_to_document(ticket)
        
        # Check labels and components
        assert "Labels: urgent, bug, backend" in doc.page_content
        assert "Components: Authentication, Database, API" in doc.page_content
    
    def test_ticket_with_empty_optional_fields(self):
        """Test ticket with empty optional fields."""
        ticket = create_sample_ticket(
            key="MINIMAL-TEST",
            description="",
            labels=[],
            components=[],
            comments=[],
            affects_versions=[],
            flags=[]
        )
        
        doc = ticket_to_document(ticket)
        
        # Should still have basic structure
        assert verify_document_structure(doc, expected_key="MINIMAL-TEST")
        assert "Key: MINIMAL-TEST" in doc.page_content
    
    def test_ticket_with_all_fields(self):
        """Test ticket with all possible fields populated."""
        ticket = create_sample_ticket(
            key="FULL-TEST",
            summary="Full featured test ticket",
            status="In Review",
            priority="Critical",
            description="Detailed description of the issue",
            comments=[
                {"author": {"displayName": "Tester"}, "body": "Test comment"}
            ],
            labels=["test", "full"],
            components=["Frontend", "Backend"],
            affects_versions=["1.0.0", "1.1.0"],
            flags=["urgent", "customer-facing"],
            issue_type="Story",
            updated="2024-01-15T10:30:00.000Z"
        )
        
        doc = ticket_to_document(ticket)
        
        # Verify all fields are present
        content_fields = count_ticket_fields_in_content(doc.page_content)
        for field, present in content_fields.items():
            assert present, f"Field {field} should be present in content"
        
        # Check specific content
        assert "Affects Versions: 1.0.0, 1.1.0" in doc.page_content
        assert "Flags: urgent, customer-facing" in doc.page_content
        assert "Issue Type: Story" in doc.page_content
        assert "Updated: 2024-01-15T10:30:00.000Z" in doc.page_content
    
    def test_metadata_structure(self, sample_ticket):
        """Test that metadata has correct structure."""
        doc = ticket_to_document(sample_ticket)
        
        expected_metadata = {
            'key': 'TEST-123',
            'status': 'Open',
            'priority': 'Medium',
            'issue_type': 'Bug'
        }
        
        for key, expected_value in expected_metadata.items():
            assert key in doc.metadata
            assert doc.metadata[key] == expected_value
    
    def test_content_length_reasonable(self, sample_ticket):
        """Test that content length is reasonable."""
        doc = ticket_to_document(sample_ticket)
        
        # Should have substantial content but not excessive
        assert len(doc.page_content) > 50, "Content should be substantial"
        assert len(doc.page_content) < 5000, "Content should not be excessive"
    
    def test_malformed_comments(self):
        """Test handling of malformed comment data."""
        ticket = create_sample_ticket(
            key="MALFORMED-TEST",
            comments=[
                "string comment",  # Not a dict
                {"author": {"displayName": "Valid"}, "body": "Valid comment"},
                {"malformed": "comment"}  # Missing expected fields
            ]
        )
        
        doc = ticket_to_document(ticket)
        
        # Should handle gracefully
        assert "string comment" in doc.page_content
        assert "Valid: Valid comment" in doc.page_content
        # Should not crash on malformed comment