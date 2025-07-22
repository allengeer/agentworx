from typing import Annotated, Dict, List

from langchain.docstore.document import Document
from langchain.tools import BaseTool
from langchain_community.utilities.jira import JiraAPIWrapper
from langchain_core.messages import ToolMessage
from langchain_core.tools import BaseToolkit, InjectedToolCallId, tool
from langgraph.prebuilt import InjectedState
from langgraph.types import Command


class MaxJiraAPIWrapper(JiraAPIWrapper):
    """A wrapper for the Jira API that is more feature rich"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def parse_issues(self, issues: Dict) -> List[dict]:
        parsed = super().parse_issues(issues)
        for i in range(len(issues.get('issues'))):
            parsed[i]["comments"] = issues.get('issues')[i].get("fields", {}).get("comment", {}).get("comments", [])
            parsed[i]["labels"] = issues.get('issues')[i].get("fields", {}).get("labels", [])
            parsed[i]["aggregatetimeoriginalestimate"] = f"{issues.get('issues')[i].get('fields', {}).get('aggregatetimeoriginalestimate', 0) or 0 / 3600}h"
            parsed[i]["aggregatetimeestimate"] = f"{issues.get('issues')[i].get('fields', {}).get('aggregatetimeestimate', 0) or 0/ 3600}h"
            parsed[i]["aggregateprogress"] = f"{issues.get('issues')[i].get('fields', {}).get('aggregateprogress', {'progress': 0}).get('progress') or 0/ 3600}h"
            parsed[i]["progress"] = f"{issues.get('issues')[i].get('fields', {}).get('progress', {'progress': 0}).get('progress') or 0 / 3600}h"
            parsed[i]["timeestimate"] = f"{issues.get('issues')[i].get('fields', {}).get('timeestimate', 0) or 0/ 3600}h"
            parsed[i]["affects_versions"] = [x.get("name") for x in issues.get('issues')[i].get("fields", {}).get("versions", [])] 
            parsed[i]["components"] = [x.get("name") for x in issues.get('issues')[i].get("fields", {}).get("components", [])] 
            parsed[i]["flags"] = [x.get("value") for x in issues.get('issues')[i].get("fields", {}).get("customfield_12310250", []) or []] 
            parsed[i]["issue_type"] = issues.get('issues')[i].get("fields", {}).get("issuetype", {}).get("name", "")
            parsed[i]["updated"] = issues.get('issues')[i].get("fields", {}).get("updated", "")
            parsed[i]["description"] = issues.get('issues')[i].get("fields", {}).get("description", "")
        return parsed
    
    def search(self, query: str, start: int = None, limit: int = None, expand: bool = None) -> str:
        issues = self.jira.jql(query, start=start,limit=limit, expand=expand)
        parsed_issues = self.parse_issues(issues)
        parsed_issues_str = (
            "Found " + str(len(parsed_issues)) + " issues:\n" + str(parsed_issues)
        )
        return parsed_issues_str


class PowerJiraToolkit(BaseToolkit):
    """This toolkit has tools that is intended for advanced usage of Jira for agentic workflows"""
    
    def __init__(self, api: JiraAPIWrapper):
        self._api = api

    def get_tools(self) -> List[BaseTool]:
        return [self._create_jql_query_tool()]
    
    def _create_jql_query_tool(self) -> BaseTool:
        """Create the jql_query tool with access to the API instance"""
        
        @tool(parse_docstring=True)
        def jql_query(jql: str, tool_call_id: Annotated[str, InjectedToolCallId],start: int = None, limit: int = None, expand: str = None) -> str:
            """
            Execute a JQL (Jira Query Language) query to search for Jira issues.
            
            This tool allows you to perform advanced searches in Jira using JQL syntax.
            It stores structured ticket data in shared memory for analysis tools and
            returns the memory key of the resulting query. Use the limit parameter to fetch ONLY as many issues as you need.
            
            Args:
                jql: The JQL query string to execute
                tool_call_id: The injected tool call id of the tool call
                start: The starting index for pagination (0-based)
                limit: Maximum number of issues to return
                expand: Optional string to expand additional fields (e.g., "changelog,comments")
            """
            
            issues = self._api.jira.jql(jql, start=start, limit=limit, expand=expand)
            parsed_issues = self._api.parse_issues(issues)
            key = f"jira.jql.{tool_call_id}"
            return Command(update={"shared_data": {key: parsed_issues}, "messages": [ToolMessage(f"The memory key for this list of issues is {key}", tool_call_id=tool_call_id)]})
        
        return jql_query

def ticket_to_document(ticket: dict) -> Document:
    """
    Convert a Jira ticket dict to a LangChain Document.
    
    This function creates a comprehensive text representation of a Jira ticket
    including all relevant fields like description, comments, labels, etc.
    
    Args:
        ticket: Dictionary containing Jira ticket data
        
    Returns:
        Document: LangChain Document with ticket content and metadata
    """
    content = f"Key: {ticket.get('key')}\n"
    content += f"Summary: {ticket.get('summary', 'N/A')}\n"
    content += f"Status: {ticket.get('status', 'N/A')}\n"
    content += f"Priority: {ticket.get('priority', 'N/A')}\n"
    
    if ticket.get('description'):
        content += f"Description: {ticket.get('description')}\n"
    
    # Include comments which are crucial for analysis
    comments = ticket.get('comments', [])
    if comments:
        content += f"Comments ({len(comments)}):\n"
        for comment in comments:
            if isinstance(comment, dict):
                # Handle cases where author might be a string or dict
                author_info = comment.get('author', {})
                if isinstance(author_info, dict):
                    author = author_info.get('displayName', 'Unknown')
                elif isinstance(author_info, str):
                    author = author_info
                else:
                    author = 'Unknown'
                    
                body = comment.get('body', '')
                content += f"  - {author}: {body}\n"
            else:
                content += f"  - {comment}\n"
    
    # Include other relevant fields from MaxJiraAPIWrapper
    if ticket.get('labels'):
        content += f"Labels: {', '.join(ticket.get('labels', []))}\n"
    if ticket.get('components'):
        content += f"Components: {', '.join(ticket.get('components', []))}\n"
    if ticket.get('affects_versions'):
        content += f"Affects Versions: {', '.join(ticket.get('affects_versions', []))}\n"
    if ticket.get('flags'):
        content += f"Flags: {', '.join(ticket.get('flags', []))}\n"
    if ticket.get('issue_type'):
        content += f"Issue Type: {ticket.get('issue_type')}\n"
    if ticket.get('updated'):
        content += f"Updated: {ticket.get('updated')}\n"
    
    metadata = {
        'key': ticket.get('key', 'N/A'),
        'status': ticket.get('status', 'N/A'),
        'priority': ticket.get('priority', 'N/A'),
        'issue_type': ticket.get('issue_type', 'N/A')
    }
    
    return Document(page_content=content, metadata=metadata)
