from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, MessagesState, END

from src.agent.nodes import llm_node, tool_node


def _should_continue(state: MessagesState) -> str:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return END


graph = StateGraph(MessagesState)
graph.add_node("llm", llm_node)
graph.add_node("tools", tool_node)
graph.set_entry_point("llm")
graph.add_conditional_edges("llm", _should_continue, {"tools": "tools", END: END})
graph.add_edge("tools", "llm")

app = graph.compile()


if __name__ == "__main__":
    print("Customer Support Agent  (type 'exit' to quit)\n")
    while True:
        question = input("You: ").strip()
        if not question or question.lower() == "exit":
            break
        result = app.invoke({"messages": [HumanMessage(content=question)]})
        print(f"Agent: {result['messages'][-1].content}\n")
