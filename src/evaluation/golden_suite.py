import json

from langchain_core.messages import HumanMessage, ToolMessage

from src.utils.snowflake_client import execute_query
from src.utils.logger import get_logger

logger = get_logger(__name__)

_GOLDEN_QUERY = """
SELECT question, expected_theme, rubric_id
FROM ANALYTICS_DB.EVALUATION.GOLDEN_CUSTOMER_SUPPORT
ORDER BY question
"""


def load_golden_suite() -> list[dict]:
    """Load golden test cases from the dbt seed table in Snowflake."""
    rows = execute_query(_GOLDEN_QUERY)
    logger.info("Loaded %d golden test cases.", len(rows))
    return [
        {
            "question": r["QUESTION"],
            "expected_theme": r["EXPECTED_THEME"],
            "rubric_id": r["RUBRIC_ID"],
        }
        for r in rows
    ]


def run_agent_on_question(question: str, agent_name: str | None = None) -> tuple[str, str]:
    """Run the LangGraph agent on a single question.

    Returns (agent_response, order_context) where order_context is the raw Snowflake
    record the agent retrieved, serialised as a JSON string (empty string if no tool call).
    """
    from src.agent.graph import build_graph

    graph = build_graph(agent_name)
    result = graph.invoke({"messages": [HumanMessage(content=question)]})

    agent_response = result["messages"][-1].content

    tool_msgs = [m for m in result["messages"] if isinstance(m, ToolMessage)]
    if tool_msgs:
        raw = tool_msgs[0].content
        order_context = raw if isinstance(raw, str) else json.dumps(raw, default=str)
    else:
        order_context = ""

    return agent_response, order_context
