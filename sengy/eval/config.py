"""
Evaluation configuration - now using unified configuration system.
"""

from typing import Any, Dict

from sengy.config import get_settings, validate_configuration


def get_evaluation_settings():
    """Get evaluation settings from unified configuration."""
    return get_settings()

# Legacy exports for backward compatibility
def get_langsmith_client_config() -> Dict[str, Any]:
    """Get LangSmith client configuration."""
    settings = get_settings()
    return {
        "api_key": settings.get_langsmith_api_key(),
        "api_url": settings.langsmith.endpoint
    }

def validate_config() -> bool:
    """Validate configuration for evaluation."""
    return validate_configuration(for_evaluation=True)

# Legacy config exports
settings = get_settings()

LANGSMITH_CONFIG = {
    "api_key": settings.get_langsmith_api_key(),
    "project_name": settings.langsmith.project_name,
    "endpoint": settings.langsmith.endpoint
}

EVALUATION_CONFIG = {
    "dataset_name": settings.evaluation.dataset_name,
    "experiment_prefix": settings.evaluation.experiment_prefix,
    "max_concurrency": settings.evaluation.max_concurrency,
    "timeout_seconds": settings.evaluation.timeout_seconds,
}

LLM_CONFIG = {
    "model": settings.openai.model,
    "temperature": settings.openai.temperature,
    "max_tokens": settings.openai.max_tokens,
    "timeout": settings.openai.timeout
}

METRICS_CONFIG = {
    "primary_metrics": [
        "engineering_relevance",
        "technical_accuracy", 
        "actionability"
    ],
    "secondary_metrics": [
        "response_length",
        "technical_depth",
        "manager_insights",
        "developer_insights"
    ],
    "thresholds": {
        "engineering_relevance": settings.evaluation.engineering_relevance_threshold,
        "technical_accuracy": settings.evaluation.technical_accuracy_threshold,
        "actionability": settings.evaluation.actionability_threshold
    }
}

SCENARIOS_CONFIG = {
    "engineering_manager": {
        "weight": 0.6,  # EM scenarios are 60% of evaluation
        "focus_areas": [
            "resource_planning",
            "risk_assessment", 
            "priority_analysis",
            "team_coordination"
        ]
    },
    "software_engineer": {
        "weight": 0.4,  # SE scenarios are 40% of evaluation  
        "focus_areas": [
            "technical_solutions",
            "implementation_details",
            "debugging_insights",
            "performance_analysis"
        ]
    }
}