from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, MessagesState, END

from src.agent.nodes import make_nodes
from src.agent.registry import DEFAULT_AGENT


def _should_continue(state: MessagesState) -> str:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return END


def build_graph(agent_name: str | None = None):
    """Build and compile a LangGraph graph for the given agent provider."""
    llm_node, tool_node = make_nodes(agent_name)

    g = StateGraph(MessagesState)
    g.add_node("llm", llm_node)
    g.add_node("tools", tool_node)
    g.set_entry_point("llm")
    g.add_conditional_edges("llm", _should_continue, {"tools": "tools", END: END})
    g.add_edge("tools", "llm")
    return g.compile()


# default graph for Streamlit chat page — uses AGENT_NAME env var or DEFAULT_AGENT
app = build_graph(DEFAULT_AGENT)


if __name__ == "__main__":
    print("Customer Support Agent  (type 'exit' to quit)\n")
    while True:
        question = input("You: ").strip()
        if not question or question.lower() == "exit":
            break
        result = app.invoke({"messages": [HumanMessage(content=question)]})
        print(f"Agent: {result['messages'][-1].content}\n")
