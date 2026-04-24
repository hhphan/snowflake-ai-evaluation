import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()
from langchain_core.messages import SystemMessage, ToolMessage
from langgraph.graph import MessagesState

from src.agent.prompts import SYSTEM_PROMPT
from src.agent.tools import query_customer_context

model = ChatOpenAI(
    model=os.environ.get("AGENT_MODEL", "gpt-4o"),
    temperature=0,
).bind_tools([query_customer_context])


def llm_node(state: MessagesState) -> dict:
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    return {"messages": [model.invoke(messages)]}


def tool_node(state: MessagesState) -> dict:
    results = []
    for call in state["messages"][-1].tool_calls:
        output = query_customer_context.invoke(call["args"])
        results.append(ToolMessage(content=str(output), tool_call_id=call["id"]))
    return {"messages": results}
