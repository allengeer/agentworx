"""
Test utilities and mocks for testing Jira functionality.
"""
from typing import Any, Dict, List
from unittest.mock import Mock, patch

from langchain.docstore.document import Document
from langchain_community.chat_models.fake import FakeListChatModel
from langchain_community.llms.fake import FakeListLLM
from langchain_core.messages import AIMessage

from .fixtures import (
    MOCK_LLM_ANALYSIS_RESPONSE,
    MOCK_LLM_SUMMARY_RESPONSE,
    MOCK_MAP_REDUCE_ANALYSIS,
    MOCK_MAP_REDUCE_SUMMARY,
)


def create_fake_llm(responses: List[str] = None) -> FakeListLLM:
    """Create a fake LLM with predefined responses."""
    if responses is None:
        responses = [
            MOCK_LLM_SUMMARY_RESPONSE,
            MOCK_LLM_ANALYSIS_RESPONSE,
            MOCK_MAP_REDUCE_SUMMARY,
            MOCK_MAP_REDUCE_ANALYSIS
        ]
    return FakeListLLM(responses=responses)


def create_fake_chat_model(responses: List[str] = None) -> FakeListChatModel:
    """Create a fake chat model with predefined responses."""
    if responses is None:
        responses = [
            MOCK_LLM_SUMMARY_RESPONSE,
            MOCK_LLM_ANALYSIS_RESPONSE, 
            MOCK_MAP_REDUCE_SUMMARY,
            MOCK_MAP_REDUCE_ANALYSIS
        ]
    return FakeListChatModel(responses=responses)


class MockStreamWriter:
    """Mock stream writer for testing."""
    
    def __init__(self):
        self.messages = []
    
    def __call__(self, message: Dict[str, Any]):
        """Capture stream messages."""
        self.messages.append(message)
        
    def get_messages(self) -> List[Dict[str, Any]]:
        """Get all captured messages."""
        return self.messages
    
    def clear(self):
        """Clear captured messages."""
        self.messages = []


def create_mock_stream_writer() -> MockStreamWriter:
    """Create a mock stream writer."""
    return MockStreamWriter()


def mock_get_stream_writer():
    """Create a context manager for mocking get_stream_writer."""
    mock_writer = create_mock_stream_writer()
    return patch('langgraph.config.get_stream_writer', return_value=mock_writer), mock_writer

def mock_get_stream_writer_for_analysis():
    """Create a context manager for mocking get_stream_writer in analysis module."""
    mock_writer = create_mock_stream_writer()
    return patch('sengy.node.analysis.get_stream_writer', return_value=mock_writer), mock_writer

def mock_get_stream_writer_for_summarise():
    """Create a context manager for mocking get_stream_writer in summarise module."""
    mock_writer = create_mock_stream_writer()
    return patch('sengy.node.summarise.get_stream_writer', return_value=mock_writer), mock_writer


def verify_document_structure(doc: Document, expected_key: str = None) -> bool:
    """Verify that a Document has the expected structure."""
    # Check that it's a Document
    if not isinstance(doc, Document):
        return False
    
    # Check required fields
    if not hasattr(doc, 'page_content') or not hasattr(doc, 'metadata'):
        return False
    
    # Check content exists
    if not doc.page_content or len(doc.page_content) < 10:
        return False
    
    # Check metadata structure
    required_metadata = ['key', 'status', 'priority', 'issue_type']
    for field in required_metadata:
        if field not in doc.metadata:
            return False
    
    # Check specific key if provided
    if expected_key and doc.metadata.get('key') != expected_key:
        return False
    
    return True


def count_ticket_fields_in_content(content: str) -> Dict[str, bool]:
    """Count which ticket fields are present in document content."""
    fields = {
        'key': 'Key:' in content,
        'summary': 'Summary:' in content,
        'status': 'Status:' in content,
        'priority': 'Priority:' in content,
        'description': 'Description:' in content,
        'comments': 'Comments' in content,
        'labels': 'Labels:' in content,
        'components': 'Components:' in content
    }
    return fields


def mock_map_reduce_chain(response: str = MOCK_MAP_REDUCE_SUMMARY):
    """Create a mock for load_summarize_chain."""
    mock_chain = Mock()
    mock_chain.invoke.return_value = {'output_text': response}
    mock_chain.run.return_value = response  # Keep for backward compatibility
    return mock_chain