#!/usr/bin/env python3
"""
Test script to verify the evaluation framework is properly set up.
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_imports():
    """Test that all required modules can be imported."""
    print("🧪 Testing Framework Imports...")
    
    try:
        from datasets import ENGINEERING_JIRA_TICKETS, ENGINEERING_MANAGER_SCENARIOS
        print("✅ Datasets import successful")
    except ImportError as e:
        print(f"❌ Datasets import failed: {e}")
        return False
    
    try:
        from sengy.config import get_settings, validate_configuration
        print("✅ Configuration import successful")
    except ImportError as e:
        print(f"❌ Configuration import failed: {e}")
        return False
    
    try:
        from langsmith_evaluator import SengyEvaluator
        print("✅ Evaluator import successful")
    except ImportError as e:
        print(f"❌ Evaluator import failed: {e}")
        return False
    
    return True


def test_configuration():
    """Test configuration system."""
    print("\n🔧 Testing Configuration System...")
    
    try:
        from sengy.config import get_settings
        settings = get_settings()
        
        print(f"✅ Settings loaded: {settings.app_name} v{settings.version}")
        print(f"   Model: {settings.openai.model}")
        print(f"   Environment: {settings.environment}")
        
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


def test_datasets():
    """Test evaluation datasets."""
    print("\n📊 Testing Evaluation Datasets...")
    
    try:
        from datasets import ENGINEERING_MANAGER_SCENARIOS, SOFTWARE_ENGINEER_SCENARIOS
        
        print(f"✅ Engineering Manager scenarios: {len(ENGINEERING_MANAGER_SCENARIOS)}")
        print(f"✅ Software Engineer scenarios: {len(SOFTWARE_ENGINEER_SCENARIOS)}")
        
        # Test scenario structure
        scenario = ENGINEERING_MANAGER_SCENARIOS[0]
        required_keys = ['scenario', 'tickets', 'query', 'expected_insights']
        
        for key in required_keys:
            if key not in scenario:
                print(f"❌ Missing key '{key}' in scenario")
                return False
        
        print("✅ Scenario structure validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Dataset test failed: {e}")
        return False


def test_evaluation_setup():
    """Test that evaluation can be set up (without running it)."""
    print("\n🚀 Testing Evaluation Setup...")
    
    try:
        # Test that we can create evaluator (may fail on API keys, that's OK)
        try:
            from langsmith_evaluator import SengyEvaluator
            evaluator = SengyEvaluator()
            print("✅ Evaluator created successfully")
            has_evaluator = True
        except ValueError as e:
            if "Missing required configuration" in str(e):
                print("⚠️  Evaluator needs API keys (expected)")
                has_evaluator = False
            else:
                raise
        
        # Test evaluation methods exist
        if has_evaluator:
            methods = ['create_dataset', 'run_evaluation', 'run_comprehensive_evaluation']
            for method in methods:
                if hasattr(evaluator, method):
                    print(f"✅ Method '{method}' available")
                else:
                    print(f"❌ Method '{method}' missing")
                    return False
        
        print("✅ Evaluation setup test passed")
        return True
        
    except Exception as e:
        print(f"❌ Evaluation setup test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🔬 Sengy Evaluation Framework Test Suite")
    print("=" * 45)
    
    tests = [
        ("Import Tests", test_imports),
        ("Configuration Tests", test_configuration), 
        ("Dataset Tests", test_datasets),
        ("Evaluation Setup Tests", test_evaluation_setup)
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        print(f"\n📋 {name}")
        print("-" * 30)
        if test_func():
            passed += 1
    
    print(f"\n🎯 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! Evaluation framework is ready.")
        
        print("\n📝 Next Steps:")
        print("1. Set API keys: OPENAI_API_KEY, LANGSMITH_API_KEY")
        print("2. Run: python eval/run_evaluation.py")
        print("3. View results in LangSmith dashboard")
        
        return True
    else:
        print("❌ Some tests failed. Please check the issues above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)