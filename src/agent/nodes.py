import os
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, ToolMessage
from langgraph.graph import MessagesState

from src.agent.prompts import SYSTEM_PROMPT
from src.agent.tools import query_customer_context
from src.agent.registry import AGENT_REGISTRY, DEFAULT_AGENT

load_dotenv()


def make_nodes(agent_name: str | None = None):
    """Return (llm_node, tool_node) configured for the given agent name."""
    name = agent_name or os.getenv("AGENT_NAME", DEFAULT_AGENT)
    factory = AGENT_REGISTRY.get(name)
    if factory is None:
        raise ValueError(f"Unknown agent: {name!r}. Available: {list(AGENT_REGISTRY)}")

    llm = factory().bind_tools([query_customer_context])

    def llm_node(state: MessagesState) -> dict:
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
        return {"messages": [llm.invoke(messages)]}

    def tool_node(state: MessagesState) -> dict:
        results = []
        for call in state["messages"][-1].tool_calls:
            output = query_customer_context.invoke(call["args"])
            results.append(ToolMessage(content=str(output), tool_call_id=call["id"]))
        return {"messages": results}

    return llm_node, tool_node
