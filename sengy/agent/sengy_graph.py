"""
SengyGraph - Intelligent routing agent that routes queries to GitHub or Jira agents.

This is the main entry point for Sengy that analyzes user queries and routes them
to the appropriate specialized agent (GitHubGraph or JiraGraph) based on the content
and intent of the query.
"""

import operator
from typing import Annotated, Dict, List, Literal, Union

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from .agent import Agent, PlanExecute
from .github_graph import GitHubGraph
from .jira_graph import JiraGraph


class RouteDecision(BaseModel):
    """Decision on which agent to route the query to."""
    
    agent: Literal["github", "jira"] = Field(
        description="Which agent to route to: 'github' for GitHub-related queries, 'jira' for Jira-related queries"
    )
    confidence: float = Field(
        description="Confidence score between 0.0 and 1.0 for the routing decision",
        ge=0.0,
        le=1.0
    )
    reasoning: str = Field(
        description="Brief explanation of why this agent was chosen"
    )


class SengyRouterState(TypedDict):
    """State for the SengyGraph router."""
    input: str
    route_decision: RouteDecision
    final_response: str
    shared_data: Annotated[Dict, operator.or_]


# Router prompt for analyzing queries and deciding which agent to use
router_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an intelligent routing system for Sengy, an AI assistant for software engineering teams.

Your job is to analyze user queries and decide whether to route them to:

1. GitHub Agent - For queries about:
   - Git repositories, commits, and code changes
   - Pull requests, code reviews, and merge activities  
   - GitHub-specific features (actions, releases, issues on GitHub)
   - Code quality, performance analysis from commits
   - Development workflow analysis
   - Repository statistics and insights
   - Commit history and author analysis

2. Jira Agent - For queries about:
   - Jira tickets, issues, and project management
   - Sprint planning and agile workflows
   - Issue tracking and bug reports
   - Jira-specific features (boards, workflows, JQL)
   - Project management and team coordination
   - Ticket analysis and reporting
   - Engineering management insights from Jira data

Decision Guidelines:
- If the query mentions GitHub, commits, pull requests, repositories, or code-specific terms -> GitHub Agent
- If the query mentions Jira, tickets, issues, sprints, or project management terms -> Jira Agent  
- If the query is ambiguous but relates to code development workflow -> GitHub Agent
- If the query is ambiguous but relates to project/issue management -> Jira Agent
- Consider the user's intent: are they asking about code/development (GitHub) or project management (Jira)?

Provide a confidence score and clear reasoning for your decision."""),
    ("human", "{query}")
])


class SengyGraph(Agent):
    """
    Main routing agent that intelligently routes queries to GitHub or Jira specialized agents.
    
    This agent analyzes incoming queries and determines whether they should be handled
    by the GitHubGraph (for repository/code analysis) or JiraGraph (for project management).
    It then executes the appropriate specialized agent and returns the results.
    """
    
    def __init__(self, llm, tools=None):
        """
        Initialize SengyGraph router.
        
        Args:
            llm: Language model for routing decisions and specialized agents
            tools: Additional tools to include (optional, passed to specialized agents)
        """
        if tools is None:
            tools = []
            
        super().__init__(llm, tools)
        
        # Initialize specialized agents
        self.github_agent = GitHubGraph(llm, tools.copy())
        self.jira_agent = JiraGraph(llm, tools.copy())
        
        # Build specialized agent graphs
        self.github_agent.build_graph()
        self.jira_agent.build_graph()
        
        # Router for making routing decisions
        self.router = router_prompt | self.llm.with_structured_output(RouteDecision)
    
    def build_graph(self):
        """Build the routing graph with decision and execution nodes."""
        try:
            # Create routing graph
            graph = StateGraph(SengyRouterState)
            
            # Add nodes
            graph.add_node("route_query", self.route_query)
            graph.add_node("execute_github", self.execute_github_agent)
            graph.add_node("execute_jira", self.execute_jira_agent)
            
            # Define edges
            graph.add_edge(START, "route_query")
            graph.add_conditional_edges(
                "route_query",
                self.decide_route,
                {
                    "github": "execute_github",
                    "jira": "execute_jira"
                }
            )
            graph.add_edge("execute_github", END)
            graph.add_edge("execute_jira", END)
            
            self.graph = graph.compile(self.checkpointer)
            
        except Exception as e:
            print(f"Error building SengyGraph: {e}")
            import traceback
            traceback.print_exc()
    
    def route_query(self, state: SengyRouterState, config=None):
        """
        Analyze the query and decide which agent to route to.
        
        Args:
            state: Current state containing the user's input query
            config: Runtime configuration
            
        Returns:
            Updated state with routing decision
        """
        query = state["input"]
        
        # Use LLM to make routing decision
        decision = self.router.invoke({"query": query}, config)
        
        return {
            "route_decision": decision,
            "shared_data": state.get("shared_data", {})
        }
    
    def decide_route(self, state: SengyRouterState) -> str:
        """
        Conditional edge function that returns which agent to execute.
        
        Args:
            state: Current state with routing decision
            
        Returns:
            Agent name to route to ("github" or "jira")
        """
        return state["route_decision"].agent
    
    def execute_github_agent(self, state: SengyRouterState, config=None):
        """
        Execute the GitHub specialized agent.
        
        Args:
            state: Current state
            config: Runtime configuration
            
        Returns:
            Updated state with GitHub agent response
        """
        query = state["input"]
        shared_data = state.get("shared_data", {})
        
        # Execute GitHub agent
        github_state = {
            "input": query,
            "plan": [],
            "past_steps": [],
            "response": "",
            "shared_data": shared_data
        }
        
        result = self.github_agent.graph.invoke(github_state, config)
        
        return {
            "final_response": result["response"],
            "shared_data": result.get("shared_data", {})
        }
    
    def execute_jira_agent(self, state: SengyRouterState, config=None):
        """
        Execute the Jira specialized agent.
        
        Args:
            state: Current state  
            config: Runtime configuration
            
        Returns:
            Updated state with Jira agent response
        """
        query = state["input"]
        shared_data = state.get("shared_data", {})
        
        # Execute Jira agent
        jira_state = {
            "input": query,
            "plan": [],
            "past_steps": [],
            "response": "",
            "shared_data": shared_data
        }
        
        result = self.jira_agent.graph.invoke(jira_state, config)
        
        return {
            "final_response": result["response"],
            "shared_data": result.get("shared_data", {})
        }
    
    def get_routing_info(self, query: str) -> RouteDecision:
        """
        Get routing decision for a query without executing the agent.
        Useful for testing and debugging routing logic.
        
        Args:
            query: User query to analyze
            
        Returns:
            RouteDecision with agent choice, confidence, and reasoning
        """
        return self.router.invoke({"query": query})
    
    def invoke(self, input_data: Union[str, Dict], config=None):
        """
        Main entry point for executing SengyGraph.
        
        Args:
            input_data: Either a string query or dict with 'input' key
            config: Runtime configuration
            
        Returns:
            Final response from the appropriate specialized agent
        """
        if isinstance(input_data, str):
            query = input_data
        else:
            query = input_data.get("input", "")
        
        initial_state = {
            "input": query,
            "route_decision": None,
            "final_response": "",
            "shared_data": {}
        }
        
        result = self.graph.invoke(initial_state, config)
        return result["final_response"]