import os
import json
import anthropic
from dotenv import load_dotenv

from src.evaluation.rubrics import RUBRIC_PROMPT, PASS_THRESHOLD
from src.utils.logger import get_logger

load_dotenv()

logger = get_logger(__name__)

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    """Return a shared Anthropic client, creating it on first call."""
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client


def score_response(question: str, agent_response: str, rubric_id: str,
                   order_context: str = "") -> dict:
    """Score one agent response with Claude. Returns dict with score, reasoning, explanation, pass."""
    client = _get_client()
    model = os.environ.get("EVAL_MODEL", "claude-sonnet-4-6")

    parts = [
        f"Rubric category: {rubric_id}",
        f"Customer question: {question}",
    ]
    if order_context:
        parts.append(f"Order record (ground truth from database):\n{order_context}")
    parts.append(f"Agent response:\n{agent_response}")
    user_content = "\n\n".join(parts)

    response = client.messages.create(
        model=model,
        max_tokens=512,
        system=[
            {
                "type": "text",
                "text": RUBRIC_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_content}],
    )

    raw = response.content[0].text.strip()
    logger.debug("Scorer raw response: %s", raw)

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("Could not parse scorer JSON: %s", raw)
        result = {"score": 0.0, "reasoning": raw, "explanation": "", "pass": False}

    result["score"] = float(result.get("score", 0.0))
    result["explanation"] = result.get("explanation", "")
    result["pass"] = bool(result.get("pass", result["score"] >= PASS_THRESHOLD))

    logger.info(
        "scored %s: %.2f (%s)",
        rubric_id,
        result["score"],
        "pass" if result["pass"] else "fail",
    )
    return result
