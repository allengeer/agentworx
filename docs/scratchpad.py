graph_builder = StateGraph(State)

def chatbot(state: State):
    return {"messages": [llm.invoke(state["messages"])]}

graph_builder.add_node("chatbot", analyze_content)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)
graph = graph_builder.compile()

def stream_graph_updates(user_input: str):
    for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}):
        for value in event.values():
            print("Assistant:", value["messages"][-1].content)

def stream_ca(dimensions: str, content: str):
    response = graph.invoke({"messages": [{"role": "user", "content": dimensions}, {"role": "user", "content": content}]})
    for name, dimension in json.loads(response["messages"][-1].content).items():
        print(f"Dimension: {name} Score: {dimension['score']} Comments: {dimension['comments']}")
        
# while True:
#     dimensions = input("Dimensions: ")
#     if dimensions.lower() in ["quit", "exit", "q"]:
#         print("Goodbye!")
#         break
#     content = input("Content: ")
#     stream_ca(dimensions, content)

# agent  = Agent(
#     llm=llm,
#     tools=[DuckDuckGoSearchRun()],
# )
# agent.build_graph()

# config = {"recursion_limit": 50}
# inputs = {"input": "can you please review the issues for the team in the current sprint?"}
# for event in agent.graph.stream(inputs, config=config):
#     for k, v in event.items():
#         if k != "__end__":
#             print(v)


class State(TypedDict):
   messages: Annotated[list, add_messages]