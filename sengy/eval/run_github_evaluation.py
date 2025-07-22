#!/usr/bin/env python3
"""
GitHub-specific evaluation script for Sengy GitHub agent.
Runs evaluation scenarios focused on GitHub repository analysis.
"""

import argparse
import os
import sys
from datetime import datetime

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sengy.eval.config import validate_config
from sengy.eval.github_evaluator import GitHubSengyEvaluator


def run_github_evaluation(dataset_name: str = None, eval_type: str = "comprehensive"):
    """
    Run Sengy GitHub evaluation with LangSmith.
    
    Args:
        dataset_name: Name for the dataset (default: auto-generated)
        eval_type: Type of evaluation ("comprehensive", "analyze", "summarize")
    """
    
    print("🔍 Sengy GitHub Agent Evaluation with LangSmith")
    print("=" * 55)
    
    # Validate configuration
    if not validate_config():
        print("❌ Configuration validation failed")
        return False
    
    print("✅ Configuration validated")
    
    # Generate dataset name if not provided
    if not dataset_name:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dataset_name = f"sengy_github_eval_{timestamp}"
    
    print(f"📊 Dataset: {dataset_name}")
    print(f"🎯 Evaluation type: {eval_type}")
    print(f"📦 Focus: GitHub repository analysis")
    print(f"🤖 Using model: o3-mini")
    
    try:
        # Initialize GitHub evaluator
        print("\n🚀 Initializing GitHub evaluator...")
        evaluator = GitHubSengyEvaluator()
        
        if eval_type == "comprehensive":
            print("🔄 Running comprehensive GitHub evaluation (analysis + summarization)...")
            results = evaluator.run_comprehensive_github_evaluation(dataset_name)
            
            print("\n📈 GitHub Evaluation Results:")
            print(f"Dataset ID: {results['dataset_id']}")
            print("GitHub analysis evaluation completed ✅")
            print("GitHub summary evaluation completed ✅")
            
        elif eval_type == "analyze":
            print("🔄 Running GitHub analysis evaluation only...")
            dataset_id = evaluator.create_github_dataset(dataset_name)
            results = evaluator.run_github_evaluation(dataset_name, "analyze")
            
            print("\n📈 GitHub Analysis Evaluation Results:")
            print(f"Dataset ID: {dataset_id}")
            print("GitHub analysis evaluation completed ✅")
            
        elif eval_type == "summarize":
            print("🔄 Running GitHub summarization evaluation only...")
            dataset_id = evaluator.create_github_dataset(dataset_name)
            results = evaluator.run_github_evaluation(dataset_name, "summarize")
            
            print("\n📈 GitHub Summarization Evaluation Results:")
            print(f"Dataset ID: {dataset_id}")
            print("GitHub summary evaluation completed ✅")
            
        else:
            print(f"❌ Unknown evaluation type: {eval_type}")
            return False
        
        print("\n🎉 GitHub evaluation completed successfully!")
        print("📊 Check LangSmith dashboard for detailed results")
        print("🔗 Focus areas: Code quality, Security, Performance, Architecture")
        
        return True
        
    except Exception as e:
        print(f"\n❌ GitHub evaluation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def show_github_scenarios():
    """Show details about the GitHub evaluation scenarios."""
    print("\n📋 GitHub Evaluation Scenarios")
    print("=" * 35)
    
    print("🏗️  Engineering Scenarios:")
    scenarios = [
        ("Code Review Analysis", "Recent commits and PRs technical improvements"),
        ("Security Vulnerability Assessment", "Security fixes and posture analysis"),
        ("Architecture Migration Planning", "Microservices migration evaluation")
    ]
    
    for i, (name, description) in enumerate(scenarios, 1):
        print(f"   {i}. {name}")
        print(f"      - {description}")
    
    print("\n👨‍💻 Development Scenarios:")
    dev_scenarios = [
        ("Performance Optimization Review", "Async processing and throughput gains"),
        ("Technical Debt Assessment", "Monolith to microservices analysis"),
        ("Incident Response Analysis", "Critical bug fixes and resolution speed")
    ]
    
    for i, (name, description) in enumerate(dev_scenarios, 1):
        print(f"   {i}. {name}")
        print(f"      - {description}")
    
    print("\n🎯 GitHub Evaluation Focus Areas:")
    focus_areas = [
        "Code quality assessment from commits",
        "Security vulnerability detection",
        "Performance optimization analysis", 
        "Architecture evolution tracking",
        "Development workflow insights",
        "Change impact assessment",
        "Best practices recognition"
    ]
    
    for area in focus_areas:
        print(f"   • {area}")


def show_github_sample_data():
    """Show sample GitHub data used in evaluations."""
    print("\n📦 Sample Repository Data")
    print("=" * 30)
    
    print("🏪 payment-service repository:")
    print("   - Memory leak fixes in webhook handlers")
    print("   - Circuit breaker pattern implementation")
    print("   - Async payment processing PR (300% improvement)")
    print("   - Performance metrics: 2.5s → 800ms latency")
    print("   - Throughput: 100 → 400 payments/second")
    
    print("\n👤 user-service repository:")
    print("   - SQL injection vulnerability fix (CVE-2024-1234)")
    print("   - Microservices migration PR (strangler fig pattern)")
    print("   - 45 files changed, 2500 additions, 800 deletions")
    print("   - Architecture: profile, auth, notification services")
    
    print("\n📊 Data Types Analyzed:")
    print("   • Commit messages and file changes")
    print("   • Pull request descriptions and reviews")
    print("   • Performance metrics and benchmarks")
    print("   • Security patches and CVE references")
    print("   • Architecture diagrams and migration plans")


def main():
    """Main entry point with CLI argument parsing."""
    
    parser = argparse.ArgumentParser(
        description="Run Sengy GitHub agent evaluation with LangSmith"
    )
    
    parser.add_argument(
        "--dataset-name", 
        type=str,
        help="Name for the evaluation dataset (auto-generated if not provided)"
    )
    
    parser.add_argument(
        "--eval-type",
        choices=["comprehensive", "analyze", "summarize"],
        default="comprehensive",
        help="Type of evaluation to run (default: comprehensive)"
    )
    
    parser.add_argument(
        "--check-config",
        action="store_true",
        help="Just check configuration and exit"
    )
    
    parser.add_argument(
        "--show-scenarios",
        action="store_true",
        help="Show GitHub evaluation scenarios and exit"
    )
    
    parser.add_argument(
        "--show-sample-data",
        action="store_true",
        help="Show sample GitHub data used in evaluation"
    )
    
    args = parser.parse_args()
    
    if args.check_config:
        print("🔍 Checking configuration...")
        if validate_config():
            print("✅ Configuration is valid for GitHub evaluation")
            return True
        else:
            print("❌ Configuration is invalid")
            return False
    
    if args.show_scenarios:
        show_github_scenarios()
        return True
        
    if args.show_sample_data:
        show_github_sample_data()
        return True
    
    return run_github_evaluation(args.dataset_name, args.eval_type)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)