#!/usr/bin/env python3
"""
Simple script to run Sengy evaluation with LangSmith using o3-mini.
"""

import argparse
import os
import sys
from datetime import datetime

from .config import validate_config
from .langsmith_evaluator import SengyEvaluator


def run_evaluation(dataset_name: str = None, eval_type: str = "comprehensive"):
    """
    Run Sengy evaluation with LangSmith.
    
    Args:
        dataset_name: Name for the dataset (default: auto-generated)
        eval_type: Type of evaluation ("comprehensive", "analyze", "summarize")
    """
    
    print("🔍 Sengy LangSmith Evaluation with o3-mini")
    print("=" * 50)
    
    # Validate configuration
    if not validate_config():
        print("❌ Configuration validation failed")
        return False
    
    print("✅ Configuration validated")
    
    # Generate dataset name if not provided
    if not dataset_name:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dataset_name = f"sengy_engineering_eval_{timestamp}"
    
    print(f"📊 Dataset: {dataset_name}")
    print(f"🎯 Evaluation type: {eval_type}")
    print(f"🤖 Using model: o3-mini")
    
    try:
        # Initialize evaluator
        print("\n🚀 Initializing evaluator...")
        evaluator = SengyEvaluator()
        
        if eval_type == "comprehensive":
            print("🔄 Running comprehensive evaluation (analysis + summarization)...")
            results = evaluator.run_comprehensive_evaluation(dataset_name)
            
            print("\n📈 Evaluation Results:")
            print(f"Dataset ID: {results['dataset_id']}")
            print("Analysis evaluation completed ✅")
            print("Summary evaluation completed ✅")
            
        elif eval_type == "analyze":
            print("🔄 Running analysis evaluation only...")
            dataset_id = evaluator.create_dataset(dataset_name)
            results = evaluator.run_evaluation(dataset_name, "analyze")
            
            print("\n📈 Analysis Evaluation Results:")
            print(f"Dataset ID: {dataset_id}")
            print("Analysis evaluation completed ✅")
            
        elif eval_type == "summarize":
            print("🔄 Running summarization evaluation only...")
            dataset_id = evaluator.create_dataset(dataset_name)
            results = evaluator.run_evaluation(dataset_name, "summarize")
            
            print("\n📈 Summarization Evaluation Results:")
            print(f"Dataset ID: {dataset_id}")
            print("Summary evaluation completed ✅")
            
        else:
            print(f"❌ Unknown evaluation type: {eval_type}")
            return False
        
        print("\n🎉 Evaluation completed successfully!")
        print("📊 Check LangSmith dashboard for detailed results")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Evaluation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point with CLI argument parsing."""
    
    parser = argparse.ArgumentParser(
        description="Run Sengy evaluation with LangSmith using o3-mini"
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
    
    args = parser.parse_args()
    
    if args.check_config:
        print("🔍 Checking configuration...")
        if validate_config():
            print("✅ Configuration is valid")
            return True
        else:
            print("❌ Configuration is invalid")
            return False
    
    return run_evaluation(args.dataset_name, args.eval_type)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)