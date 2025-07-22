from typing import Dict, List

from langchain_community.agent_toolkits.jira.toolkit import JiraToolkit
from langchain_community.utilities.jira import JiraAPIWrapper

from ..node.analysis import analyze_content_tool
from ..node.jira import MaxJiraAPIWrapper, PowerJiraToolkit
from ..node.summarise import summarise_content_tool
from ..node.utils import DateTimeToolkit
from .agent import Agent


class JiraGraph(Agent):
    def __init__(self, llm, tools=[]):
        # if tools contains JiraToolkit, we don't need to add it again
        # if not any(isinstance(tool, JiraToolkit) for tool in tools):
        #     tools = tools + list(filter(lambda x: x.name in ['get_projects'], JiraToolkit.from_jira_api_wrapper(JiraAPIWrapper()).get_tools()))

        # Add PowerJiraToolkit with jql_query tool if not already present
        if not any(tool.name == "jql_query" for tool in tools):
            power_jira_toolkit = PowerJiraToolkit(MaxJiraAPIWrapper())
            tools.extend(power_jira_toolkit.get_tools())

        # if tools contains analyze_content or summarise_content, we don't need to add them again
        if not any(tool.name == "analyze_content_tool" for tool in tools):
            tools.append(analyze_content_tool)
        if not any(tool.name== "summarise_content_tool" for tool in tools):
            tools.append(summarise_content_tool)
        tools.extend(DateTimeToolkit().get_tools())
        super().__init__(llm, tools)
        

    def build_agent(self):
        super().build_agent()
        # self.graph.add_node("analysis", analyze_content)
        # self.graph.add_node("summarisation", summarise_content)
        # self.graph.add_edge("agent", "analysis")
        # self.graph.add_edge("agent", "summarisation")
        # self.graph.add_edge("summarisation", "agent")
        # self.graph.add_edge("analysis", "agent")