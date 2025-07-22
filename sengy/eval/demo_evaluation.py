#!/usr/bin/env python3
"""
Demo evaluation script that shows how LangSmith evaluation works.
Can run with or without API keys to demonstrate the framework.
"""

import json
import os
import sys
from typing import Any, Dict

from ..config import validate_configuration
from .datasets import ENGINEERING_MANAGER_SCENARIOS, SOFTWARE_ENGINEER_SCENARIOS


def demo_tool_responses() -> Dict[str, Any]:
    """
    Demo function that simulates what our analysis tool would return.
    This shows the expected format without requiring API calls.
    """
    return {
        "messages": [{
            "content": """
            **Technical Analysis - Engineering Perspective**
            
            **Priority Assessment:**
            - High priority: Critical performance issue affecting 50K+ users
            - Database N+1 query pattern identified in UserAuth.findByToken()
            - Missing composite index on auth_tokens table causing 5-10s delays
            
            **Technical Solution:**
            - Implement eager loading for related data queries
            - Create composite index: auth_tokens(user_id, token_hash, expires_at)
            - Database migration required with proper downtime planning
            
            **Resource Requirements:**
            - Senior backend developer: 2 days implementation
            - DBA: Index migration and monitoring
            - QA: Performance testing validation
            
            **Risk Assessment:**
            - Low implementation risk (standard optimization)
            - High impact: Immediate user experience improvement
            - Deployment risk: Minimal if proper migration strategy used
            
            **Implementation Timeline:**
            1. Create database migration (Day 1)
            2. Implement query optimization (Day 1-2)
            3. Performance testing (Day 2)
            4. Staged deployment with monitoring (Day 3)
            """
        }]
    }


def simulate_evaluation_run():
    """
    Simulate running the evaluation to show what results would look like.
    """
    print("🎯 Sengy LangSmith Evaluation Demo")
    print("=" * 50)
    
    # Check configuration
    print("🔍 Configuration Check:")
    has_basic_config = validate_configuration(for_evaluation=False)
    has_eval_config = validate_configuration(for_evaluation=True)
    
    if not has_basic_config:
        print("⚠️  Missing basic configuration (OpenAI API key)")
        print("   This demo will simulate responses")
    
    if not has_eval_config:
        print("⚠️  Missing evaluation configuration (LangSmith API key)")
        print("   This demo will simulate evaluation results")
    
    print("\n📊 Evaluation Scenarios:")
    print(f"   Engineering Manager scenarios: {len(ENGINEERING_MANAGER_SCENARIOS)}")
    print(f"   Software Engineer scenarios: {len(SOFTWARE_ENGINEER_SCENARIOS)}")
    
    # Simulate running evaluation on first scenario
    scenario = ENGINEERING_MANAGER_SCENARIOS[0]
    print(f"\n🧪 Running Demo Evaluation:")
    print(f"   Scenario: {scenario['scenario']}")
    print(f"   Query: {scenario['query'][:100]}...")
    print(f"   Tickets: {len(scenario['tickets'])} Jira tickets")
    
    # Simulate tool response
    print("\n🤖 Simulated Tool Response:")
    demo_response = demo_tool_responses()
    analysis_content = demo_response["messages"][0]["content"]
    print(analysis_content[:500] + "...")
    
    # Simulate evaluation metrics
    print("\n📈 Simulated Evaluation Metrics:")
    
    # Engineering relevance (check for expected insights)
    expected_insights = scenario["expected_insights"]
    insights_found = 3  # Simulated
    relevance_score = insights_found / len(expected_insights)
    print(f"   Engineering Relevance: {relevance_score:.2f}")
    print(f"   - Found {insights_found}/{len(expected_insights)} expected insights")
    
    # Technical accuracy (simulated LLM evaluation)
    accuracy_score = 0.85  # Simulated
    print(f"   Technical Accuracy: {accuracy_score:.2f}")
    print(f"   - LLM-evaluated technical correctness")
    
    # Actionability (keyword analysis)
    actionable_score = 0.78  # Simulated
    print(f"   Actionability: {actionable_score:.2f}")
    print(f"   - Contains specific technical recommendations")
    
    # Overall assessment
    overall_score = (relevance_score + accuracy_score + actionable_score) / 3
    print(f"\n🎯 Overall Score: {overall_score:.2f}")
    
    # Threshold comparison
    print("\n✅ Threshold Analysis:")
    thresholds = {
        "engineering_relevance": 0.7,
        "technical_accuracy": 0.8,
        "actionability": 0.6
    }
    
    scores = {
        "engineering_relevance": relevance_score,
        "technical_accuracy": accuracy_score,
        "actionability": actionable_score
    }
    
    for metric, threshold in thresholds.items():
        score = scores[metric]
        status = "✅ PASS" if score >= threshold else "❌ FAIL"
        print(f"   {metric}: {score:.2f} >= {threshold} {status}")
    
    return overall_score


def show_real_evaluation_setup():
    """Show how to set up and run real evaluation with API keys."""
    print("\n🚀 Real Evaluation Setup Guide")
    print("=" * 40)
    
    print("1. Set up API keys:")
    print("   export OPENAI_API_KEY='your-openai-key'")
    print("   export LANGSMITH_API_KEY='your-langsmith-key'")
    
    print("\n2. Run configuration check:")
    print("   python scripts/configure.py")
    
    print("\n3. Run full evaluation:")
    print("   python eval/run_evaluation.py")
    
    print("\n4. Run specific evaluation type:")
    print("   python eval/run_evaluation.py --eval-type analyze")
    print("   python eval/run_evaluation.py --eval-type summarize")
    
    print("\n5. View results:")
    print("   - LangSmith dashboard: https://smith.langchain.com")
    print("   - Experiment comparisons and detailed traces")
    print("   - Metric breakdowns and failure analysis")


def show_dataset_details():
    """Show details about the evaluation datasets."""
    print("\n📋 Evaluation Dataset Details")
    print("=" * 35)
    
    print("🏗️  Engineering Manager Scenarios:")
    for i, scenario in enumerate(ENGINEERING_MANAGER_SCENARIOS, 1):
        print(f"   {i}. {scenario['scenario']}")
        print(f"      - {len(scenario['tickets'])} tickets")
        print(f"      - {len(scenario['expected_insights'])} expected insights")
    
    print("\n👨‍💻 Software Engineer Scenarios:")
    for i, scenario in enumerate(SOFTWARE_ENGINEER_SCENARIOS, 1):
        print(f"   {i}. {scenario['scenario']}")
        print(f"      - {len(scenario['tickets'])} tickets")
        print(f"      - {len(scenario['expected_insights'])} expected insights")
    
    print("\n🎯 Evaluation Focus Areas:")
    focus_areas = [
        "Technical debt assessment",
        "Performance debugging", 
        "Security vulnerability analysis",
        "Infrastructure scaling",
        "Sprint planning analysis",
        "Incident response prioritization"
    ]
    
    for area in focus_areas:
        print(f"   • {area}")


def main():
    """Main demo function."""
    print("🔬 Sengy LangSmith Evaluation Framework Demo")
    print("=" * 50)
    
    # Show dataset details
    show_dataset_details()
    
    # Run simulated evaluation
    score = simulate_evaluation_run()
    
    # Show real setup guide
    show_real_evaluation_setup()
    
    print(f"\n🎉 Demo Complete!")
    print(f"   Simulated overall score: {score:.2f}")
    print(f"   Framework ready for real evaluation with API keys")
    
    return score


if __name__ == "__main__":
    main()