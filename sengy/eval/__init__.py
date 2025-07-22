"""
Sengy evaluation package - LangSmith-based evaluation for engineering scenarios.
"""

from .config import (
    EVALUATION_CONFIG,
    LANGSMITH_CONFIG,
    LLM_CONFIG,
    METRICS_CONFIG,
    validate_config,
)
from .datasets import (
    ENGINEERING_JIRA_TICKETS,
    ENGINEERING_MANAGER_SCENARIOS,
    EVALUATION_DIMENSIONS,
    SOFTWARE_ENGINEER_SCENARIOS,
)
from .langsmith_evaluator import SengyEvaluator

__all__ = [
    "SengyEvaluator",
    "ENGINEERING_JIRA_TICKETS", 
    "ENGINEERING_MANAGER_SCENARIOS",
    "SOFTWARE_ENGINEER_SCENARIOS", 
    "EVALUATION_DIMENSIONS",
    "LANGSMITH_CONFIG",
    "EVALUATION_CONFIG",
    "LLM_CONFIG", 
    "METRICS_CONFIG",
    "validate_config"
]