"""
LangSmith evaluation test harness for Sengy.
Tests the agent's performance with real LLMs on engineering-focused scenarios.
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

from sengy.agent.jira_graph import JiraGraph
from sengy.node.analysis import analyze_content_tool
from sengy.node.summarise import summarise_content_tool

from .config import LLM_CONFIG, validate_config
from .datasets import (
    ENGINEERING_JIRA_TICKETS,
    ENGINEERING_MANAGER_SCENARIOS,
    EVALUATION_DIMENSIONS,
    SOFTWARE_ENGINEER_SCENARIOS,
)


class SengyEvaluator:
    """
    Evaluation harness for Sengy agent using LangSmith.
    Tests analysis and summarization capabilities with engineering-focused scenarios.
    """
    
    def __init__(self, langsmith_api_key: Optional[str] = None):
        # Validate configuration
        if not validate_config():
            raise ValueError("Missing required configuration. Please check environment variables.")
            
        self.client = Client(api_key=langsmith_api_key)
        self.llm = init_chat_model(LLM_CONFIG["model"])
        self.jira_graph = JiraGraph(self.llm)
        
    def create_dataset(self, dataset_name: str) -> str:
        """Create a LangSmith dataset with engineering scenarios."""
        
        # Combine all scenarios
        all_scenarios = []
        
        # Add engineering manager scenarios
        for scenario in ENGINEERING_MANAGER_SCENARIOS:
            all_scenarios.append({
                "inputs": {
                    "query": scenario["query"],
                    "tickets": json.dumps(scenario["tickets"]),
                    "scenario_type": "engineering_manager",
                    "scenario_name": scenario["scenario"]
                },
                "outputs": {
                    "expected_insights": scenario["expected_insights"]
                }
            })
            
        # Add software engineer scenarios  
        for scenario in SOFTWARE_ENGINEER_SCENARIOS:
            all_scenarios.append({
                "inputs": {
                    "query": scenario["query"], 
                    "tickets": json.dumps(scenario["tickets"]),
                    "scenario_type": "software_engineer",
                    "scenario_name": scenario["scenario"]
                },
                "outputs": {
                    "expected_insights": scenario["expected_insights"]
                }
            })
            
        # Create dataset in LangSmith
        dataset = self.client.create_dataset(
            dataset_name=dataset_name,
            description="Engineering-focused Jira analysis scenarios for Sengy evaluation"
        )
        
        # Add examples to dataset
        for scenario in all_scenarios:
            self.client.create_example(
                dataset_id=dataset.id,
                inputs=scenario["inputs"],
                outputs=scenario["outputs"]
            )
            
        return dataset.id
    
    def analyze_tickets_tool_wrapper(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Wrapper function for analyze_content_tool to work with LangSmith evaluation."""
        query = inputs["query"]
        tickets_json = inputs["tickets"]
        
        # Extract dimensions from query - for evaluation we'll use standard engineering dimensions
        dimensions = ["technical_complexity", "business_impact", "implementation_risk", "priority"]
        
        # Parse tickets from JSON string
        import json
        try:
            tickets = json.loads(tickets_json)
        except:
            tickets = tickets_json
        
        # Create mock state with shared data
        mock_state = {
            "shared_data": {
                "eval_tickets": tickets
            }
        }
        
        # Mock stream writer to avoid LangGraph context issues
        def mock_writer(message):
            pass  # Do nothing for evaluation
        
        with patch('sengy.node.analysis.get_stream_writer', return_value=mock_writer):
            # Get the underlying function from the tool
            analyze_func = analyze_content_tool.func
            result = analyze_func(dimensions, "eval_tickets", mock_state)
        
        return {
            "analysis": result["messages"][0].content,
            "dimensions_analyzed": dimensions,
            "scenario_type": inputs.get("scenario_type", "unknown")
        }
    
    def summarize_tickets_tool_wrapper(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Wrapper function for summarise_content_tool to work with LangSmith evaluation."""
        tickets_json = inputs["tickets"]
        
        # Use engineering-focused dimensions
        dimensions = "technical_scope,business_impact,implementation_timeline,resource_requirements"
        
        # Parse tickets from JSON string
        import json
        try:
            tickets = json.loads(tickets_json)
        except:
            tickets = tickets_json
        
        # Create mock state with shared data
        mock_state = {
            "shared_data": {
                "eval_tickets": tickets
            }
        }
        
        # Mock stream writer to avoid LangGraph context issues
        def mock_writer(message):
            pass  # Do nothing for evaluation
        
        with patch('sengy.node.summarise.get_stream_writer', return_value=mock_writer):
            # Get the underlying function from the tool
            summarize_func = summarise_content_tool.func
            result = summarize_func(dimensions, memory_key="eval_tickets", state=mock_state)
        
        return {
            "summary": result["messages"][0].content,
            "dimensions_summarized": dimensions.split(","),
            "scenario_type": inputs.get("scenario_type", "unknown")
        }

    def engineering_relevance_evaluator(self, run: Run, example: Example) -> Dict[str, Any]:
        """
        Custom evaluator that checks if the analysis is relevant to engineering teams.
        """
        if not run.outputs or not example.outputs:
            return {"key": "engineering_relevance", "score": 0, "reason": "Missing outputs"}
            
        analysis = run.outputs.get("analysis", "")
        expected_insights = example.outputs.get("expected_insights", [])
        scenario_type = example.inputs.get("scenario_type", "")
        
        # Count how many expected insights are mentioned in the analysis
        insights_found = 0
        for insight in expected_insights:
            if any(keyword.lower() in analysis.lower() for keyword in insight.split()[:3]):
                insights_found += 1
                
        relevance_score = insights_found / len(expected_insights) if expected_insights else 0
        
        return {
            "key": "engineering_relevance",
            "score": relevance_score,
            "reason": f"Found {insights_found}/{len(expected_insights)} expected engineering insights",
            "comment": f"Analysis relevance for {scenario_type} scenario"
        }
    
    def technical_accuracy_evaluator(self, run: Run, example: Example) -> Dict[str, Any]:
        """
        Evaluator that uses an LLM to assess technical accuracy of the analysis.
        """
        if not run.outputs:
            return {"key": "technical_accuracy", "score": 0, "reason": "No outputs to evaluate"}
            
        analysis = run.outputs.get("analysis", "")
        tickets = example.inputs.get("tickets", "")
        query = example.inputs.get("query", "")
        
        evaluation_prompt = f"""
        Evaluate the technical accuracy of this Jira ticket analysis for software engineering teams.
        
        Original Query: {query}
        
        Ticket Data: {tickets}
        
        Analysis Generated: {analysis}
        
        Rate the technical accuracy on a scale of 0.0 to 1.0, considering:
        - Are technical details correctly identified?
        - Are proposed solutions technically sound?
        - Are risks and dependencies accurately assessed?
        - Are recommendations actionable for engineering teams?
        
        Respond with just a number between 0.0 and 1.0.
        """
        
        try:
            response = self.llm.invoke([HumanMessage(content=evaluation_prompt)])
            score = float(response.content.strip())
            score = max(0.0, min(1.0, score))  # Clamp between 0 and 1
            
            return {
                "key": "technical_accuracy", 
                "score": score,
                "reason": f"LLM-evaluated technical accuracy: {score}"
            }
        except Exception as e:
            return {
                "key": "technical_accuracy",
                "score": 0.0, 
                "reason": f"Evaluation failed: {str(e)}"
            }
    
    def actionability_evaluator(self, run: Run, example: Example) -> Dict[str, Any]:
        """
        Evaluator that checks if the analysis provides actionable recommendations.
        """
        if not run.outputs:
            return {"key": "actionability", "score": 0, "reason": "No outputs"}
            
        analysis = run.outputs.get("analysis", "").lower()
        
        # Look for actionable keywords
        actionable_keywords = [
            "implement", "configure", "create", "add", "remove", "update", 
            "optimize", "refactor", "migrate", "deploy", "test", "monitor",
            "should", "need to", "recommend", "suggest", "next steps"
        ]
        
        actionable_count = sum(1 for keyword in actionable_keywords if keyword in analysis)
        
        # Also check for specific technical recommendations
        technical_recommendations = [
            "index", "query", "circuit breaker", "scaling", "migration",
            "testing", "monitoring", "security", "performance"
        ]
        
        technical_count = sum(1 for term in technical_recommendations if term in analysis)
        
        # Score based on presence of actionable language and technical specificity
        actionability_score = min(1.0, (actionable_count * 0.1) + (technical_count * 0.15))
        
        return {
            "key": "actionability",
            "score": actionability_score,
            "reason": f"Found {actionable_count} actionable terms, {technical_count} technical recommendations"
        }
    
    def run_evaluation(self, dataset_name: str, target_function: str = "analyze") -> Dict[str, Any]:
        """
        Run evaluation on the specified dataset.
        
        Args:
            dataset_name: Name of the LangSmith dataset
            target_function: Either "analyze" or "summarize"
        """
        
        # Select the appropriate function
        if target_function == "analyze":
            target_func = self.analyze_tickets_tool_wrapper
        elif target_function == "summarize":
            target_func = self.summarize_tickets_tool_wrapper
        else:
            raise ValueError("target_function must be 'analyze' or 'summarize'")
            
        # Get dataset
        datasets = list(self.client.list_datasets(dataset_name=dataset_name))
        if not datasets:
            raise ValueError(f"Dataset '{dataset_name}' not found")
            
        dataset = datasets[0]
        
        # Run evaluation
        results = evaluate(
            target_func,
            data=dataset,
            evaluators=[
                self.engineering_relevance_evaluator,
                self.technical_accuracy_evaluator, 
                self.actionability_evaluator
            ],
            experiment_prefix=f"sengy_{target_function}_eval",
            description=f"Evaluation of Sengy {target_function} tool with engineering scenarios"
        )
        
        return results
    
    def run_comprehensive_evaluation(self, dataset_name: str = "sengy_engineering_eval") -> Dict[str, Any]:
        """
        Run comprehensive evaluation covering both analysis and summarization.
        """
        
        print(f"Creating dataset: {dataset_name}")
        dataset_id = self.create_dataset(dataset_name)
        print(f"Dataset created with ID: {dataset_id}")
        
        print("Running analysis evaluation...")
        analysis_results = self.run_evaluation(dataset_name, "analyze")
        
        print("Running summarization evaluation...")
        summary_results = self.run_evaluation(dataset_name, "summarize")
        
        return {
            "dataset_id": dataset_id,
            "analysis_evaluation": analysis_results,
            "summary_evaluation": summary_results
        }


def main():
    """Run the evaluation suite."""
    
    # Ensure LangSmith API key is set
    if not os.environ.get("LANGSMITH_API_KEY"):
        print("Please set LANGSMITH_API_KEY environment variable")
        return
        
    evaluator = SengyEvaluator()
    
    print("Starting Sengy evaluation with LangSmith...")
    results = evaluator.run_comprehensive_evaluation()
    
    print("\n=== Evaluation Complete ===")
    print(f"Dataset ID: {results['dataset_id']}")
    print(f"Analysis results: {results['analysis_evaluation']}")
    print(f"Summary results: {results['summary_evaluation']}")
    
    return results


if __name__ == "__main__":
    main()