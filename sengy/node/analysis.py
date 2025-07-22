import json
from typing import Annotated, Dict, List

from langchain.chains.summarize import load_summarize_chain
from langchain.docstore.document import Document
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from langchain_core.messages import AIMessage  # Import MessagesState and AIMessage
from langchain_core.tools import tool
from langgraph.config import get_stream_writer
from langgraph.graph.message import MessagesState
from langgraph.prebuilt import InjectedState
from pydantic import BaseModel, Field

from ..config import DEBUG, get_llm
from .jira import ticket_to_document


class Analysis:
    def __init__(self, dimensions: dict):
        self.dimensions = dimensions

    def set_dimension(self, name: str, score: int, comments: str):
        self.dimensions[name] = {'score': score, 'comments': comments}
        
    def get_dimension(self, name: str):
        return self.dimensions.get(name, None)
    
analysis_prompt = (
    "You are analyzing the content provided in the variety of dimensions requested."
    "For each dimension, provide a score from 1 to 10, where 1 is the lowest and 10 is the highest."
    "Also, provide comments for each score to explain your reasoning."
    "The dimensions to analyze are: \n\n{dimensions}\n\n"
    "The content to analyze is: \n\n{content}\n\n"
    "{format_instructions}\n"
)

class DimensionAnalysis(BaseModel):
    name: str = Field(description="The name of the dimension being analyzed.")
    score: int = Field(ge=1, le=10, description="The score for the dimension, from 1 to 10.")
    comments: str = Field(description="Comments explaining the score given for the dimension.")

class AnalysisModel(BaseModel):
    dimensions: list[DimensionAnalysis] = Field(
        description="A list of dimensions analyzed, each with a name, score, and comments."
    )

parser = PydanticOutputParser(pydantic_object=AnalysisModel)

@tool
def analyze_content_tool(dimensions: List[str], memory_key: str, state: Annotated[Dict, InjectedState]) -> dict:
    """
    DIMSCORE(dimensions, content)
    Analyze and score content in different dimensions using map-reduce approach.
    
    This tool can handle both plain text content and structured Jira ticket data.
    It first checks shared memory for structured ticket data from jql_query tool.
    For large datasets (multiple tickets), it uses map-reduce for optimal processing.
    Provides scores from 1-10 for each dimension with detailed analysis.
    
    Args:
        dimensions: List of dimensions to analyze and score
        memory_key: Memory key of the content to analyze
        state: Injected LangGraph state containing shared data
        
    Returns:
        dict: Analysis results with scores and insights for each dimension
    """
    writer = get_stream_writer()
    content = None
    if memory_key in state.get("shared_data", {}):
        content = state["shared_data"][memory_key]
        writer({"custom_data": f"[bold green]SHARED DATA FOUND[/bold green]: Retrieved {len(content)} from shared memory"})
    
    # If we have structured ticket data, use map-reduce approach
    if content:
        dimensions_str = ",".join(dimensions)
        writer({"custom_data": f"[bold blue]MAP-REDUCE ANALYSIS[/bold blue]: Processing {len(content)} items {len(dimensions)} dimensions"})
        
        if isinstance(content, list):
            # Convert tickets to Documents using shared function
            try: 
                documents = [ticket_to_document(ticket) for ticket in content]
            except:
                documents = [Document(page_content=str(ticket)) for ticket in content]
        else:
            documents = [Document(page_content=str(content))]
        
        # Create custom prompts for dimensional scoring
        map_template = f"""
        Analyze and score the following Jira ticket across these dimensions: {dimensions_str}
        
        For each dimension:
        1. Provide a score from 1 to 10 (where 1 is lowest, 10 is highest)
        2. Explain your reasoning with specific examples from the ticket
        
        Ticket Content:
        {{text}}
        
        Output format for each dimension:
        Dimension: [name]
        Score: [1-10]
        Reasoning: [detailed explanation]
        """
        
        reduce_template = f"""
        Below are individual ticket analyses across these dimensions: {dimensions_str}
        
        Combine these analyses to provide:
        1. Average scores for each dimension across all tickets
        2. Score distribution insights (highs, lows, patterns)
        3. Key themes and patterns identified
        4. Aggregate insights for each dimension
        
        Individual Ticket Analyses:
        {{text}}
        
        Provide a comprehensive dimensional analysis with aggregate scores and insights.
        """
        
        # Create the map-reduce chain
        map_prompt = PromptTemplate(template=map_template, input_variables=["text"])
        reduce_prompt = PromptTemplate(template=reduce_template, input_variables=["text"])
        
        chain = load_summarize_chain(
            llm=get_llm(),
            chain_type="map_reduce",
            map_prompt=map_prompt,
            combine_prompt=reduce_prompt,
            verbose=DEBUG
        )
        
        writer({"custom_data": f"[blue]Running map-reduce analysis across {len(documents)} documents[/blue]"})
        
        # Run the chain
        result = chain.invoke(documents)['output_text']
        
        writer({"custom_data": f"[bold blue]MAP-REDUCE ANALYSIS COMPLETE[/bold blue]"})
        
        return {"messages": [AIMessage(content=result)]}
    return {"messages": [AIMessage(content="Failure to analyze content")]}
