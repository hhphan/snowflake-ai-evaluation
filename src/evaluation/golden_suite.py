from langchain_core.messages import HumanMessage

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


def run_agent_on_question(question: str, agent_name: str | None = None) -> str:
    """Run the LangGraph agent on a single question and return its final text response."""
    from src.agent.graph import build_graph

    graph = build_graph(agent_name)
    result = graph.invoke({"messages": [HumanMessage(content=question)]})
    return result["messages"][-1].content
