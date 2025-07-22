"""
GitHub-specific evaluation test harness for Sengy.
Tests the agent's performance analyzing GitHub repositories, commits, and pull requests.
"""

import json
import os
from typing import Any, Dict, List, Optional
from unittest.mock import patch

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
from langsmith import Client
from langsmith.evaluation import evaluate
from langsmith.schemas import Example, Run

from sengy.agent.github_graph import GitHubGraph
from sengy.node.analysis import analyze_content_tool
from sengy.node.summarise import summarise_content_tool
from sengy.node.github import github_data_to_document

from sengy.eval.config import LLM_CONFIG, validate_config
from sengy.eval.github_datasets import (
    GITHUB_REPOSITORIES_DATA,
    GITHUB_ENGINEERING_SCENARIOS,
    GITHUB_DEVELOPMENT_SCENARIOS,
    GITHUB_EVALUATION_DIMENSIONS,
)


class GitHubSengyEvaluator:
    """
    Evaluation harness for Sengy GitHub agent using LangSmith.
    Tests analysis and summarization capabilities with GitHub-focused scenarios.
    """
    
    def __init__(self, langsmith_api_key: Optional[str] = None):
        # Validate configuration
        if not validate_config():
            raise ValueError("Missing required configuration. Please check environment variables.")
            
        self.client = Client(api_key=langsmith_api_key)
        self.llm = init_chat_model(LLM_CONFIG["model"])
        self.github_graph = GitHubGraph(self.llm)
        
    def create_github_dataset(self, dataset_name: str) -> str:
        """Create a LangSmith dataset with GitHub engineering scenarios."""
        
        # Combine all GitHub scenarios
        all_scenarios = []
        
        # Add GitHub engineering scenarios
        for scenario in GITHUB_ENGINEERING_SCENARIOS:
            all_scenarios.append({
                "inputs": {
                    "query": scenario["query"],
                    "repo_data": json.dumps(scenario["repo_data"]),
                    "scenario_type": "github_engineering",
                    "scenario_name": scenario["scenario"]
                },
                "outputs": {
                    "expected_insights": scenario["expected_insights"]
                }
            })
            
        # Add GitHub development scenarios  
        for scenario in GITHUB_DEVELOPMENT_SCENARIOS:
            all_scenarios.append({
                "inputs": {
                    "query": scenario["query"], 
                    "repo_data": json.dumps(scenario["repo_data"]),
                    "scenario_type": "github_development",
                    "scenario_name": scenario["scenario"]
                },
                "outputs": {
                    "expected_insights": scenario["expected_insights"]
                }
            })
            
        # Create dataset in LangSmith
        dataset = self.client.create_dataset(
            dataset_name=dataset_name,
            description="GitHub-focused repository analysis scenarios for Sengy evaluation"
        )
        
        # Add examples to dataset
        for scenario in all_scenarios:
            self.client.create_example(
                dataset_id=dataset.id,
                inputs=scenario["inputs"],
                outputs=scenario["outputs"]
            )
            
        return dataset.id
    
    def analyze_github_data_wrapper(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Wrapper function for analyzing GitHub data with Sengy tools."""
        query = inputs["query"]
        repo_data_json = inputs["repo_data"]
        
        # Extract dimensions from query - for evaluation we'll use GitHub-specific dimensions
        dimensions = ["code_quality", "security_impact", "performance_impact", "architecture_changes"]
        
        # Parse repo data from JSON string
        try:
            if isinstance(repo_data_json, str):
                repo_data = json.loads(repo_data_json)
            else:
                repo_data = repo_data_json
        except (json.JSONDecodeError, TypeError):
            repo_data = repo_data_json
        
        # Convert GitHub data to documents for analysis
        all_data = []
        
        # Add commits
        if "commits" in repo_data:
            all_data.extend(repo_data["commits"])
            
        # Add pull requests  
        if "pull_requests" in repo_data:
            all_data.extend(repo_data["pull_requests"])
        
        # Convert to documents using GitHub utility
        documents = github_data_to_document(all_data)
        
        # Create mock state with shared data
        mock_state = {
            "shared_data": {
                "github_eval_data": documents
            }
        }
        
        # Mock stream writer to avoid LangGraph context issues
        def mock_writer(message):
            pass  # Do nothing for evaluation
        
        with patch('sengy.node.analysis.get_stream_writer', return_value=mock_writer):
            # Get the underlying function from the tool
            analyze_func = analyze_content_tool.func
            result = analyze_func(dimensions, "github_eval_data", mock_state)
        
        return {
            "analysis": result["messages"][0].content,
            "dimensions_analyzed": dimensions,
            "scenario_type": inputs.get("scenario_type", "unknown"),
            "data_types_analyzed": ["commits", "pull_requests"] if "commits" in repo_data and "pull_requests" in repo_data else ["commits"] if "commits" in repo_data else ["pull_requests"]
        }
    
    def summarize_github_data_wrapper(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Wrapper function for summarizing GitHub data with Sengy tools."""
        repo_data_json = inputs["repo_data"]
        
        # Use GitHub-specific dimensions for summarization
        dimensions = "code_changes,performance_impact,security_changes,architecture_evolution"
        
        # Parse repo data from JSON string
        try:
            if isinstance(repo_data_json, str):
                repo_data = json.loads(repo_data_json)
            else:
                repo_data = repo_data_json
        except (json.JSONDecodeError, TypeError):
            repo_data = repo_data_json
        
        # Convert GitHub data to documents
        all_data = []
        if "commits" in repo_data:
            all_data.extend(repo_data["commits"])
        if "pull_requests" in repo_data:
            all_data.extend(repo_data["pull_requests"])
        
        documents = github_data_to_document(all_data)
        
        # Create mock state with shared data
        mock_state = {
            "shared_data": {
                "github_eval_data": documents
            }
        }
        
        # Mock stream writer to avoid LangGraph context issues
        def mock_writer(message):
            pass  # Do nothing for evaluation
        
        with patch('sengy.node.summarise.get_stream_writer', return_value=mock_writer):
            # Get the underlying function from the tool
            summarize_func = summarise_content_tool.func
            result = summarize_func(dimensions, memory_key="github_eval_data", state=mock_state)
        
        return {
            "summary": result["messages"][0].content,
            "dimensions_summarized": dimensions.split(","),
            "scenario_type": inputs.get("scenario_type", "unknown")
        }

    def github_code_quality_evaluator(self, run: Run, example: Example) -> Dict[str, Any]:
        """
        Custom evaluator that checks if the analysis identifies code quality aspects.
        """
        if not run.outputs or not example.outputs:
            return {"key": "code_quality_assessment", "score": 0, "reason": "Missing outputs"}
            
        analysis = run.outputs.get("analysis", "")
        expected_insights = example.outputs.get("expected_insights", [])
        
        # Look for code quality indicators
        code_quality_keywords = [
            "memory leak", "performance", "optimization", "refactor", "code quality",
            "best practices", "maintainability", "technical debt", "architecture"
        ]
        
        quality_mentions = sum(1 for keyword in code_quality_keywords if keyword.lower() in analysis.lower())
        
        # Count expected insights related to code quality
        quality_insights_found = 0
        for insight in expected_insights:
            if any(keyword in insight.lower() for keyword in code_quality_keywords):
                if any(keyword.lower() in analysis.lower() for keyword in insight.split()[:4]):
                    quality_insights_found += 1
                    
        total_quality_insights = sum(1 for insight in expected_insights 
                                   if any(keyword in insight.lower() for keyword in code_quality_keywords))
        
        quality_score = quality_insights_found / total_quality_insights if total_quality_insights > 0 else 0
        keyword_score = min(1.0, quality_mentions * 0.2)
        
        final_score = (quality_score + keyword_score) / 2
        
        return {
            "key": "code_quality_assessment",
            "score": final_score,
            "reason": f"Found {quality_insights_found}/{total_quality_insights} quality insights, {quality_mentions} quality keywords",
            "comment": f"Code quality analysis for GitHub scenario"
        }
    
    def github_security_awareness_evaluator(self, run: Run, example: Example) -> Dict[str, Any]:
        """
        Evaluator that checks if the analysis identifies security-related changes.
        """
        if not run.outputs:
            return {"key": "security_awareness", "score": 0, "reason": "No outputs to evaluate"}
            
        analysis = run.outputs.get("analysis", "").lower()
        expected_insights = example.outputs.get("expected_insights", [])
        
        # Security-related keywords
        security_keywords = [
            "security", "vulnerability", "sql injection", "cve", "exploit",
            "authentication", "authorization", "encryption", "validation",
            "sanitization", "escape", "parameterized", "input validation"
        ]
        
        security_mentions = sum(1 for keyword in security_keywords if keyword in analysis)
        
        # Check for security-related expected insights
        security_insights_found = 0
        total_security_insights = 0
        
        for insight in expected_insights:
            if any(keyword in insight.lower() for keyword in security_keywords):
                total_security_insights += 1
                if any(keyword.lower() in analysis for keyword in insight.split()[:4]):
                    security_insights_found += 1
        
        if total_security_insights > 0:
            insight_score = security_insights_found / total_security_insights
        else:
            # If no security insights expected, score based on whether security keywords are present
            insight_score = 1.0 if security_mentions > 0 else 0.5
            
        keyword_score = min(1.0, security_mentions * 0.3)
        final_score = (insight_score + keyword_score) / 2
        
        return {
            "key": "security_awareness",
            "score": final_score,
            "reason": f"Found {security_insights_found}/{total_security_insights} security insights, {security_mentions} security terms"
        }
    
    def github_performance_understanding_evaluator(self, run: Run, example: Example) -> Dict[str, Any]:
        """
        Evaluator that checks if the analysis understands performance implications.
        """
        if not run.outputs:
            return {"key": "performance_understanding", "score": 0, "reason": "No outputs"}
            
        analysis = run.outputs.get("analysis", "").lower()
        expected_insights = example.outputs.get("expected_insights", [])
        
        # Performance-related keywords
        performance_keywords = [
            "performance", "latency", "throughput", "optimization", "async",
            "memory", "cpu", "scaling", "load", "response time", "bottleneck",
            "cache", "queue", "concurrent", "parallel", "efficiency"
        ]
        
        performance_mentions = sum(1 for keyword in performance_keywords if keyword in analysis)
        
        # Look for specific performance metrics mentioned
        metric_indicators = [
            "ms", "seconds", "seconds", "requests/second", "concurrent", 
            "p95", "p99", "latency", "throughput", "%"
        ]
        
        metrics_found = sum(1 for indicator in metric_indicators if indicator in analysis)
        
        # Check performance-related expected insights
        performance_insights_found = 0
        total_performance_insights = 0
        
        for insight in expected_insights:
            if any(keyword in insight.lower() for keyword in performance_keywords):
                total_performance_insights += 1
                if any(keyword.lower() in analysis for keyword in insight.split()[:4]):
                    performance_insights_found += 1
        
        insight_score = performance_insights_found / total_performance_insights if total_performance_insights > 0 else 0
        keyword_score = min(1.0, performance_mentions * 0.2)
        metric_score = min(1.0, metrics_found * 0.3)
        
        final_score = (insight_score + keyword_score + metric_score) / 3
        
        return {
            "key": "performance_understanding", 
            "score": final_score,
            "reason": f"Found {performance_insights_found}/{total_performance_insights} performance insights, {performance_mentions} perf terms, {metrics_found} metrics"
        }
    
    def github_technical_accuracy_evaluator(self, run: Run, example: Example) -> Dict[str, Any]:
        """
        Evaluator that uses an LLM to assess technical accuracy of GitHub analysis.
        """
        if not run.outputs:
            return {"key": "technical_accuracy", "score": 0, "reason": "No outputs to evaluate"}
            
        analysis = run.outputs.get("analysis", "")
        repo_data = example.inputs.get("repo_data", "")
        query = example.inputs.get("query", "")
        
        evaluation_prompt = f"""
        Evaluate the technical accuracy of this GitHub repository analysis for software engineering teams.
        
        Original Query: {query}
        
        Repository Data: {repo_data}
        
        Analysis Generated: {analysis}
        
        Rate the technical accuracy on a scale of 0.0 to 1.0, considering:
        - Are commit messages and code changes correctly interpreted?
        - Are performance metrics and improvements accurately identified?
        - Are security issues and fixes properly understood?
        - Are architectural changes and their implications correctly assessed?
        - Are technical recommendations sound for the observed changes?
        
        Respond with just a number between 0.0 and 1.0.
        """
        
        try:
            response = self.llm.invoke([HumanMessage(content=evaluation_prompt)])
            score = float(response.content.strip())
            score = max(0.0, min(1.0, score))  # Clamp between 0 and 1
            
            return {
                "key": "technical_accuracy", 
                "score": score,
                "reason": f"LLM-evaluated technical accuracy for GitHub analysis: {score}"
            }
        except Exception as e:
            return {
                "key": "technical_accuracy",
                "score": 0.0, 
                "reason": f"Evaluation failed: {str(e)}"
            }
    
    def run_github_evaluation(self, dataset_name: str, target_function: str = "analyze") -> Dict[str, Any]:
        """
        Run evaluation on the specified GitHub dataset.
        
        Args:
            dataset_name: Name of the LangSmith dataset
            target_function: Either "analyze" or "summarize"
        """
        
        # Select the appropriate function
        if target_function == "analyze":
            target_func = self.analyze_github_data_wrapper
        elif target_function == "summarize":
            target_func = self.summarize_github_data_wrapper
        else:
            raise ValueError("target_function must be 'analyze' or 'summarize'")
            
        # Get dataset
        datasets = list(self.client.list_datasets(dataset_name=dataset_name))
        if not datasets:
            raise ValueError(f"Dataset '{dataset_name}' not found")
            
        dataset = datasets[0]
        
        # Run evaluation with GitHub-specific evaluators
        results = evaluate(
            target_func,
            data=dataset,
            evaluators=[
                self.github_code_quality_evaluator,
                self.github_security_awareness_evaluator,
                self.github_performance_understanding_evaluator,
                self.github_technical_accuracy_evaluator
            ],
            experiment_prefix=f"sengy_github_{target_function}_eval",
            description=f"Evaluation of Sengy GitHub {target_function} tool with repository scenarios"
        )
        
        return results
    
    def run_comprehensive_github_evaluation(self, dataset_name: str = "sengy_github_eval") -> Dict[str, Any]:
        """
        Run comprehensive GitHub evaluation covering both analysis and summarization.
        """
        
        print(f"Creating GitHub dataset: {dataset_name}")
        dataset_id = self.create_github_dataset(dataset_name)
        print(f"GitHub dataset created with ID: {dataset_id}")
        
        print("Running GitHub analysis evaluation...")
        analysis_results = self.run_github_evaluation(dataset_name, "analyze")
        
        print("Running GitHub summarization evaluation...")
        summary_results = self.run_github_evaluation(dataset_name, "summarize")
        
        return {
            "dataset_id": dataset_id,
            "github_analysis_evaluation": analysis_results,
            "github_summary_evaluation": summary_results
        }


def main():
    """Run the GitHub evaluation suite."""
    
    # Ensure LangSmith API key is set
    if not os.environ.get("LANGSMITH_API_KEY"):
        print("Please set LANGSMITH_API_KEY environment variable")
        return
        
    evaluator = GitHubSengyEvaluator()
    
    print("Starting Sengy GitHub evaluation with LangSmith...")
    results = evaluator.run_comprehensive_github_evaluation()
    
    print("\n=== GitHub Evaluation Complete ===")
    print(f"Dataset ID: {results['dataset_id']}")
    print(f"Analysis results: {results['github_analysis_evaluation']}")
    print(f"Summary results: {results['github_summary_evaluation']}")
    
    return results


if __name__ == "__main__":
    main()