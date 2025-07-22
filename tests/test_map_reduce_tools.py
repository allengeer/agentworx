"""
Unit tests for map-reduce summarization and analysis tools.
"""
import json
from unittest.mock import Mock, patch

import pytest

from sengy.node.analysis import analyze_content_tool
from sengy.node.summarise import summarise_content_tool

from .fixtures import (
    MOCK_MAP_REDUCE_ANALYSIS,
    MOCK_MAP_REDUCE_SUMMARY,
    large_ticket_dataset,
    small_ticket_dataset,
)
from .test_utils import (
    create_fake_llm,
    mock_get_stream_writer,
    mock_get_stream_writer_for_analysis,
    mock_get_stream_writer_for_summarise,
    mock_map_reduce_chain,
)


def get_tool_function(tool_obj):
    """Extract the underlying function from a LangChain tool."""
    return tool_obj.func


class TestMapReduceSummariseTickets:
    """Test the summarise_content_tool tool."""
    
    @patch('sengy.node.summarise.load_summarize_chain')
    def test_summarise_small_dataset(self, mock_chain_loader, small_ticket_dataset):
        """Test summarization with small dataset using memory_key."""
        # Setup mocks
        mock_chain = mock_map_reduce_chain(MOCK_MAP_REDUCE_SUMMARY)
        mock_chain_loader.return_value = mock_chain
        
        patch_obj, mock_writer = mock_get_stream_writer_for_summarise()
        with patch_obj:
            # Create mock state with shared data
            mock_state = {
                "shared_data": {
                    "test_tickets": small_ticket_dataset
                }
            }
            
            # Get the underlying function and call it directly
            summarise_func = get_tool_function(summarise_content_tool)
            result = summarise_func("priority,complexity", memory_key="test_tickets", state=mock_state)
            
            # Verify result structure
            assert "messages" in result
            assert len(result["messages"]) == 1
            assert MOCK_MAP_REDUCE_SUMMARY in result["messages"][0].content
    
    @patch('sengy.node.summarise.load_summarize_chain')
    def test_summarise_large_dataset(self, mock_chain_loader, large_ticket_dataset):
        """Test summarization with large dataset (25 tickets) using memory_key."""
        # Setup mocks
        mock_chain = mock_map_reduce_chain(MOCK_MAP_REDUCE_SUMMARY)
        mock_chain_loader.return_value = mock_chain
        
        patch_obj, mock_writer = mock_get_stream_writer_for_summarise()
        with patch_obj:
            # Create mock state with shared data
            mock_state = {
                "shared_data": {
                    "large_tickets": large_ticket_dataset
                }
            }
            
            # Get the underlying function and call it directly
            summarise_func = get_tool_function(summarise_content_tool)
            result = summarise_func("priority,complexity,impact", memory_key="large_tickets", state=mock_state)
            
            # Verify chain was called with documents
            mock_chain.invoke.assert_called_once()
            args = mock_chain.invoke.call_args[0]
            documents = args[0]
            
            # Should have 25 documents (one per ticket)
            assert len(documents) == 25
            
            # Each document should have proper structure
            for doc in documents:
                assert hasattr(doc, 'page_content')
                assert hasattr(doc, 'metadata')
                assert len(doc.page_content) > 10
    
    def test_fallback_to_content_parameter(self):
        """Test fallback to content parameter when memory_key not found."""
        patch_obj, mock_writer = mock_get_stream_writer_for_summarise()
        with patch_obj:
            # Empty state
            mock_state = {"shared_data": {}}
            
            summarise_func = get_tool_function(summarise_content_tool)
            result = summarise_func("priority", content="test content", memory_key="missing_key", state=mock_state)
            
            # Should process as plain text content
            assert "messages" in result
            assert len(result["messages"]) == 1
            # Should contain analysis of the content
            assert "priority" in result["messages"][0].content.lower()
    
    def test_plain_text_content_processing(self):
        """Test handling of plain text content (not structured tickets)."""
        patch_obj, mock_writer = mock_get_stream_writer_for_summarise()
        with patch_obj:
            mock_state = {
                "shared_data": {
                    "plain_text": "This is some plain text content for analysis"
                }
            }
            
            summarise_func = get_tool_function(summarise_content_tool)
            result = summarise_func("priority", memory_key="plain_text", state=mock_state)
            
            # Should process as plain text
            assert "messages" in result
            assert len(result["messages"]) == 1
            # Should contain summary content
            assert "priority" in result["messages"][0].content.lower()
    
    @patch('sengy.node.summarise.load_summarize_chain')
    def test_stream_writer_messages(self, mock_chain_loader, small_ticket_dataset):
        """Test that progress messages are sent to stream writer."""
        mock_chain = mock_map_reduce_chain(MOCK_MAP_REDUCE_SUMMARY)
        mock_chain_loader.return_value = mock_chain
        
        patch_obj, mock_writer = mock_get_stream_writer_for_summarise()
        with patch_obj:
            mock_state = {
                "shared_data": {
                    "test_tickets": small_ticket_dataset
                }
            }
            
            summarise_func = get_tool_function(summarise_content_tool)
            summarise_func("priority", memory_key="test_tickets", state=mock_state)
            
            # Should have sent progress messages
            messages = mock_writer.get_messages()
            assert len(messages) > 0
            
            # Check for expected message types
            message_texts = [msg.get("custom_data", "") for msg in messages]
            assert any("MAP-REDUCE SUMMARY" in text for text in message_texts)


class TestMapReduceAnalyzeTickets:
    """Test the analyze_content_tool tool."""
    
    @patch('sengy.node.analysis.load_summarize_chain')
    def test_analyze_small_dataset(self, mock_chain_loader, small_ticket_dataset):
        """Test analysis with small dataset using memory_key."""
        # Setup mocks
        mock_chain = mock_map_reduce_chain(MOCK_MAP_REDUCE_ANALYSIS)
        mock_chain_loader.return_value = mock_chain
        
        patch_obj, mock_writer = mock_get_stream_writer_for_analysis()
        with patch_obj:
            # Create mock state with shared data
            mock_state = {
                "shared_data": {
                    "test_tickets": small_ticket_dataset
                }
            }
            
            # Get the underlying function and call it directly
            analyze_func = get_tool_function(analyze_content_tool)
            result = analyze_func(["priority", "complexity"], "test_tickets", mock_state)
            
            # Verify result structure
            assert "messages" in result
            assert len(result["messages"]) == 1
            assert MOCK_MAP_REDUCE_ANALYSIS in result["messages"][0].content
    
    @patch('sengy.node.analysis.load_summarize_chain')
    def test_analyze_large_dataset(self, mock_chain_loader, large_ticket_dataset):
        """Test analysis with large dataset using memory_key."""
        mock_chain = mock_map_reduce_chain(MOCK_MAP_REDUCE_ANALYSIS)
        mock_chain_loader.return_value = mock_chain
        
        patch_obj, mock_writer = mock_get_stream_writer_for_analysis()
        with patch_obj:
            mock_state = {
                "shared_data": {
                    "large_tickets": large_ticket_dataset
                }
            }
            
            analyze_func = get_tool_function(analyze_content_tool)
            result = analyze_func(["priority", "complexity", "urgency"], "large_tickets", mock_state)
            
            # Verify chain was called
            mock_chain.invoke.assert_called_once()
            args = mock_chain.invoke.call_args[0]
            documents = args[0]
            
            # Should process all tickets
            assert len(documents) == 25
    
    @patch('sengy.node.analysis.load_summarize_chain')
    def test_analysis_prompt_templates(self, mock_chain_loader, small_ticket_dataset):
        """Test that correct prompt templates are used for analysis."""
        mock_chain_loader.return_value = mock_map_reduce_chain()
        
        patch_obj, mock_writer = mock_get_stream_writer_for_analysis()
        with patch_obj:
            mock_state = {
                "shared_data": {
                    "test_tickets": small_ticket_dataset
                }
            }
            
            analyze_func = get_tool_function(analyze_content_tool)
            analyze_func(["priority", "complexity"], "test_tickets", mock_state)
            
            # Verify load_summarize_chain was called with correct parameters
            mock_chain_loader.assert_called_once()
            call_kwargs = mock_chain_loader.call_args[1]
            
            assert call_kwargs['chain_type'] == 'map_reduce'
            assert 'map_prompt' in call_kwargs
            assert 'combine_prompt' in call_kwargs
            assert 'verbose' in call_kwargs
    
    def test_dimensions_parameter_handling(self):
        """Test that dimensions parameter is handled correctly."""
        patch_obj, mock_writer = mock_get_stream_writer_for_analysis()
        with patch_obj:
            mock_state = {
                "shared_data": {
                    "empty_tickets": []
                }
            }
            
            analyze_func = get_tool_function(analyze_content_tool)
            
            # Test with different dimension formats
            result = analyze_func([], "empty_tickets", mock_state)
            # Should handle empty dimensions list
            
            result = analyze_func(["single"], "empty_tickets", mock_state)
            # Should handle single dimension
            
            result = analyze_func(["one", "two", "three"], "empty_tickets", mock_state)
            # Should handle multiple dimensions
    
    @patch('sengy.node.analysis.load_summarize_chain')
    def test_stream_progress_messages(self, mock_chain_loader, large_ticket_dataset):
        """Test progress messages for large dataset analysis."""
        mock_chain_loader.return_value = mock_map_reduce_chain()
        
        patch_obj, mock_writer = mock_get_stream_writer_for_analysis()
        with patch_obj:
            mock_state = {
                "shared_data": {
                    "large_tickets": large_ticket_dataset
                }
            }
            
            analyze_func = get_tool_function(analyze_content_tool)
            analyze_func(["priority", "complexity"], "large_tickets", mock_state)
            
            messages = mock_writer.get_messages()
            message_texts = [msg.get("custom_data", "") for msg in messages]
            
            # Should show processing information
            assert any("MAP-REDUCE ANALYSIS" in text for text in message_texts)
            assert any("25" in text for text in message_texts)
            assert any("2 dimensions" in text for text in message_texts)