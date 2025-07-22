
import operator
import traceback
from typing import Annotated, Dict, List, Tuple, Union  # Import MessagesState

from langchain.schema.runnable import RunnableConfig
from langchain_core.messages import trim_messages
from langchain_core.messages.utils import count_tokens_approximately, trim_messages
from langchain_core.prompts import ChatPromptTemplate
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.config import get_stream_writer
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, create_react_agent
from langgraph.prebuilt.chat_agent_executor import AgentState
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from ..config import DEBUG
from ..node.utils import get_todays_date


class PlanExecute(TypedDict):
    input: str
    plan: List[str]
    past_steps: Annotated[List[Tuple], operator.add]
    response: str
    shared_data: Annotated[Dict, operator.or_]

class AgentStateWithSharedData(AgentState):
    shared_data: Annotated[Dict, operator.or_]

class State(TypedDict):
   messages: Annotated[list, add_messages]


class Plan(BaseModel):
    """Plan to follow in future"""

    steps: List[str] = Field(
        description="different steps to follow, should be in sorted order"
    )


class Response(BaseModel):
    """Response to user."""

    response: str


class Act(BaseModel):
    """Action to perform."""

    action: Union[Response, Plan] = Field(
        description="Action to perform. If you want to respond to user, use Response. "
        "If you need to further use tools to get the answer, use Plan."
    )

planner_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """For the given objective, come up with a simple step by step plan. \
This plan should involve individual tasks, that if executed correctly will yield the correct answer. Do not add any superfluous steps. \
The result of the final step should be the final answer. Make sure that each step has all the information needed - do not skip steps. This plan \
should be about the information you need to gather and the actions you must perform to get the answer. It should not include steps to take in \
a user interface or on the web. """,
        ),
        ("placeholder", "{messages}"),
    ])

replanner_prompt = ChatPromptTemplate.from_template(
    """For the given objective, come up with a simple step by step plan. \
This plan should involve individual tasks, that if executed correctly will yield the correct answer. Do not add any superfluous steps. \
The result of the final step should be the final answer and should answer the users question directly on its own.

Make sure that each step has all the information needed - do not skip steps.

Your objective was this:
{input}

Your original plan was this:
{plan}

You have currently done the follow steps:
{past_steps}

Update your plan accordingly. You have two options:

1. If you have enough information to fully answer the user's question with a comprehensive response, use the Response action to provide the final answer.

2. If you still need to gather more information or perform additional analysis to fully answer the question, use the Plan action with the remaining steps needed.

Only provide a Response as a complete, thorough answer that answers the users question directly on its own. Otherwise, continue with a Plan. Only add steps to the plan that still NEED to be done. Do not return previously done steps as part of the plan."""
)


class Agent:
    def __init__(self, llm, tools=[get_todays_date]):
        self.llm = llm
        llm.bind_tools(tools)
        self.tools = tools
        self.checkpointer = InMemorySaver()
        self.graph = None

    def build_graph(self):
        try:
            graph = StateGraph(PlanExecute)
            planner_prompt.partial_variables["tools"] = ", ".join([tool.name for tool in self.tools])
            planner_prompt.extend(("system","{tools}"))
            replanner_prompt.partial_variables["tools"] = ", ".join([tool.name for tool in self.tools])
            replanner_prompt.extend(("system","{tools}"))
            self.replanner = replanner_prompt | self.llm.with_structured_output(Act)
            self.planner = planner_prompt | self.llm.with_structured_output(Plan)
            self.build_agent()
            graph.add_node("planner", self.plan_step)
            graph.add_node("agent", self.execute_step)
            graph.add_node("replan", self.replan_step)
            graph.add_edge(START, "planner")
            graph.add_edge("planner", "agent")
            graph.add_edge("agent", "replan")
            graph.add_conditional_edges(
                "replan",
                self.should_end,
                ["agent", END],
            )
            self.graph = graph.compile(self.checkpointer)
        except:
            print("Error building graph:", traceback.format_exc())

    def build_agent(self):
        self.toolnode = ToolNode(self.tools, handle_tool_errors=False)
        self.agent_executor = create_react_agent(
                self.llm,
                tools=self.toolnode,
                debug=DEBUG,
                pre_model_hook=self.pre_model_hook,
                checkpointer=InMemorySaver(),
                state_schema=AgentStateWithSharedData
            )
        return
    
    def execute_step(self, state: PlanExecute, config: RunnableConfig):
        event_writer = get_stream_writer()
        plan = state["plan"]
        plan_str = "\n".join(f"{i + 1}. {step}" for i, step in enumerate(plan))
        task = plan[0]
        task_formatted = f"""For the following plan:{plan_str}\n\nYou are tasked with executing step {1}. Execute the task as completely and thoroughly as possible. The perference is to be exhaustive in completion of the task and the data we provide., {task}."""
        agent_response = self.agent_executor.invoke(
            {"messages": [("user", task_formatted)], "shared_data": state["shared_data"]},
            config,
            stream_mode=["values", "custom"]
        )
        if any(x[0] == "custom" for x in agent_response):
            customs = [x[1] for x in agent_response if x[0] == "custom"]
            for custom in customs:
                event_writer(custom)
        
        return {
            "past_steps": [(task, agent_response[-1][1]["messages"][-1].content)],
            "shared_data": agent_response[-1][1]["shared_data"]
        }

    def plan_step(self, state: PlanExecute, config: RunnableConfig):
        plan = self.planner.invoke({"messages": [("user", state["input"])]}, config)
        return {"plan": plan.steps, "response": None }


    def replan_step(self, state: PlanExecute, config: RunnableConfig):
        output = self.replanner.invoke(state, config)
        if isinstance(output.action, Response):
            return {"response": output.action.response}
        else:
            return {"plan": output.action.steps}

    def should_end(self, state: PlanExecute):
        if "response" in state and state["response"]:
            return END
        else:
            return "agent"
        
    # This function will be called every time before the node that calls LLM
    def pre_model_hook(self, state):
        trimmed_messages = trim_messages(
            state["messages"],
            strategy="last",
            token_counter=count_tokens_approximately,
            max_tokens=384,
            start_on="human",
            include_system=True,
            end_on=("human", "tool"),
        )
        return {"llm_input_messages": trimmed_messages}