import json
from typing import Annotated, Dict

from langchain.chains.summarize import load_summarize_chain
from langchain.docstore.document import Document
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from langchain_core.messages import (  # Import MessagesState
    AIMessage,
    merge_message_runs,
)
from langchain_core.tools import tool
from langgraph.config import get_stream_writer
from langgraph.graph.message import MessagesState
from langgraph.prebuilt import InjectedState
from pydantic import BaseModel, Field

from ..config import DEBUG, get_llm
from .jira import ticket_to_document


class Summary:
    def __init__(self, dimensions: dict):
        self.dimensions = dimensions

    def set_dimension(self, name: str, summary: str):
        self.dimensions[name] = summary
        
    def get_dimension(self, name: str):
        return self.dimensions.get(name, None)
    
summary_prompt = (
    "You are summarizing the content provided in the variety of dimensions requested."
    "For each dimension, provide a summary that captures the essence of the content with respect to that dimension."
    "The dimensions to analyze are: \n\n{dimensions}\n\n"
    "The content to analyze is: \n\n{content}\n\n"
    "{format_instructions}\n"
)

class DimensionSummary(BaseModel):
    name: str = Field(description="The name of the dimension being summarised.")
    summary: str = Field(description="The summary of the content with respect to the dimension.")

class SummaryModel(BaseModel):
    dimensions: list[DimensionSummary] = Field(
        description="A list of dimensions summarized, each with a name and summary."
    )

parser = PydanticOutputParser(pydantic_object=SummaryModel)

def summarise_content(state: MessagesState) -> dict:
    dimensions = state["messages"][0].content
    content = state["messages"][-1].content
    summary = Summary(dimensions={})
    prompt = PromptTemplate(template=summary_prompt, input_variables=["dimensions", "content"], partial_variables={"format_instructions": parser.get_format_instructions()})
    response = (
        get_llm().with_structured_output(SummaryModel).invoke(
            [{"role": "user", "content": prompt.format(dimensions=dimensions, content=content)}]
        )        
    )
    for dimension in response.dimensions:
        summary.set_dimension(dimension.name, dimension.summary)
    return {"messages": [AIMessage(content=json.dumps(summary.dimensions, indent=2))]}

@tool
def summarise_content_tool(dimensions: str, content: str = None, memory_key: str = None, state: Annotated[Dict, InjectedState] = None) -> dict:
    """
    Summarize content based on specified dimensions using map-reduce approach.
    
    This tool can handle both plain text content and structured Jira ticket data.
    For large datasets (multiple tickets), it uses map-reduce for optimal processing.

    If the content to be summarized has been stored in shared memory with a memory key, use the memory_key parameter to retrieve it.
    If the content is not in shared memory, use the content parameter to provide the content to summarize.
    
    Args:
        dimensions: Comma-separated list of dimensions to summarize
        content: Optional parameter that provides plain text content to summarize
        memory_key: Optional parameter that provides Memory Key in shared memory to retrieve content from
        state: Injected LangGraph state containing shared data
        
    Returns:
        dict: Summary results with dimensional analysis
    """
    writer = get_stream_writer()
    
    # First, check for structured ticket data in shared memory
    tickets = None
    if memory_key:
        if memory_key in state.get("shared_data", {}):
            content = state['shared_data'][memory_key]
            writer({"custom_data": f"[bold green]CONTENT FOUND[/bold green]: Retrieved {memory_key} from shared memory"})
    
    # If we have structured ticket data, use map-reduce approach
    if content and isinstance(content, list) and len(content) > 0:
        writer({"custom_data": f"[bold green]MAP-REDUCE SUMMARY[/bold green]: Processing {len(content)} items"})
        
        try: 
            documents = [ticket_to_document(ticket) for ticket in content]
        except:
            documents = [Document(page_content=str(ticket)) for ticket in content]
        
        # Create custom prompts for dimensional analysis
        map_template = f"""
        Analyze the following content across these dimensions: {dimensions}
        
        For each dimension, provide insights and key points from this item.
        
        Content:
        {{text}}
        
        Provide a structured analysis covering each dimension.
        """
        
        reduce_template = f"""
        Below are analyses of individual content items across these dimensions: {dimensions}
        
        Combine these analyses into a comprehensive summary that:
        1. Synthesizes insights across all items for each dimension
        2. Identifies patterns and trends
        3. Provides aggregate insights
        
        Individual Item Analyses:
        {{text}}
        
        Create a final dimensional summary.
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
        
        writer({"custom_data": f"[blue]Running map-reduce across {len(documents)} documents[/blue]"})
        
        # Run the chain
        result = chain.invoke(documents)['output_text']
        
        writer({"custom_data": f"[bold green]MAP-REDUCE COMPLETE[/bold green]"})
        return {"messages": [AIMessage(content=result)]}
    else:
        # Plain text content - use original approach
        writer({"custom_data": f"[bold blue]TEXT SUMMARY[/bold blue]: Processing text content"})
        
        from langchain_core.messages import HumanMessage
        state = MessagesState(messages=[HumanMessage(content=dimensions), HumanMessage(content=content)])
        result = summarise_content(state)
        writer({"custom_data": f"[bold blue]TEXT SUMMARY COMPLETE[/bold blue]"})
    return result

