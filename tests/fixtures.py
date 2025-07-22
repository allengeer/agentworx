"""
Test fixtures for Jira ticket testing.
"""
from typing import Dict, List

import pytest


def create_sample_ticket(
    key: str = "TEST-123",
    summary: str = "Sample ticket",
    status: str = "Open",
    priority: str = "Medium",
    description: str = "Sample description",
    comments: List[Dict] = None,
    labels: List[str] = None,
    components: List[str] = None,
    **kwargs
) -> Dict:
    """Create a sample Jira ticket for testing."""
    if comments is None:
        comments = [
            {
                "author": {"displayName": "John Doe"},
                "body": "Initial comment"
            }
        ]
    
    if labels is None:
        labels = ["test", "sample"]
    
    if components is None:
        components = ["Backend", "API"]
    
    ticket = {
        "key": key,
        "summary": summary,
        "status": status,
        "priority": priority,
        "description": description,
        "comments": comments,
        "labels": labels,
        "components": components,
        "affects_versions": kwargs.get("affects_versions", ["1.0.0"]),
        "flags": kwargs.get("flags", []),
        "issue_type": kwargs.get("issue_type", "Bug"),
        "updated": kwargs.get("updated", "2024-01-01T12:00:00.000Z")
    }
    
    return ticket


@pytest.fixture
def sample_ticket():
    """Single sample ticket fixture."""
    return create_sample_ticket()


@pytest.fixture
def large_ticket_dataset():
    """Create a larger dataset of tickets for batch testing."""
    tickets = []
    
    # Create diverse tickets
    ticket_types = ["Bug", "Feature", "Task", "Story"]
    priorities = ["Low", "Medium", "High", "Critical"]
    statuses = ["Open", "In Progress", "Review", "Done"]
    
    for i in range(25):  # Create 25 tickets for testing batch processing
        ticket = create_sample_ticket(
            key=f"TEST-{1000 + i}",
            summary=f"Sample ticket {i + 1}",
            status=statuses[i % len(statuses)],
            priority=priorities[i % len(priorities)],
            issue_type=ticket_types[i % len(ticket_types)],
            description=f"This is a detailed description for ticket {i + 1}. " * 3,
            comments=[
                {
                    "author": {"displayName": f"User {j}"},
                    "body": f"Comment {j} on ticket {i + 1}"
                }
                for j in range((i % 3) + 1)  # Variable number of comments
            ],
            labels=[f"label-{i}", "common-label"],
            components=[f"Component-{i % 5}"]
        )
        tickets.append(ticket)
    
    return tickets


@pytest.fixture
def small_ticket_dataset():
    """Small dataset for basic testing."""
    return [
        create_sample_ticket(
            key="SMALL-1",
            summary="First ticket",
            description="First ticket description"
        ),
        create_sample_ticket(
            key="SMALL-2", 
            summary="Second ticket",
            description="Second ticket description"
        ),
        create_sample_ticket(
            key="SMALL-3",
            summary="Third ticket", 
            description="Third ticket description"
        )
    ]


# Mock responses for testing
MOCK_LLM_SUMMARY_RESPONSE = """
{
  "dimensions": [
    {
      "name": "Priority",
      "summary": "Mixed priority levels with focus on high-priority items"
    },
    {
      "name": "Complexity", 
      "summary": "Moderate complexity across most tickets"
    }
  ]
}
"""

MOCK_LLM_ANALYSIS_RESPONSE = """
Dimension: Priority
Score: 7
Reasoning: Most tickets show high priority based on urgency indicators

Dimension: Complexity
Score: 6
Reasoning: Moderate complexity with some technical depth required
"""

MOCK_MAP_REDUCE_SUMMARY = """
# Summary Analysis

## Priority Dimension
The ticket dataset shows a balanced distribution of priorities with emphasis on urgent items requiring immediate attention.

## Complexity Dimension  
Overall complexity is moderate, with most tickets requiring standard development effort.
"""

MOCK_MAP_REDUCE_ANALYSIS = """
# Aggregate Analysis Results

## Priority (Average Score: 7.2)
- High priority items dominate the dataset
- Score distribution: 3 tickets at 8-9, 2 tickets at 5-6

## Complexity (Average Score: 6.1)
- Moderate complexity overall
- Most tickets require standard development effort
"""