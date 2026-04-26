import os
import time
import uuid
import argparse
from datetime import datetime, timezone
from dotenv import load_dotenv

from src.evaluation.golden_suite import load_golden_suite, run_agent_on_question
from src.evaluation.scorer import score_response
from src.agent.registry import AGENT_REGISTRY, DEFAULT_AGENT, get_model_name, get_model_name
from src.utils.snowflake_client import get_connection
from src.utils.logger import get_logger

load_dotenv()

logger = get_logger(__name__)

_WRITE_SQL = """
INSERT INTO ANALYTICS_DB.EVALUATION.EVAL_RESULTS
    (RUN_ID, AGENT_NAME, MODEL_NAME, QUESTION, AGENT_RESPONSE, SCORE, REASONING, PASS, RUBRIC_ID, RUN_TIMESTAMP)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS ANALYTICS_DB.EVALUATION.EVAL_RESULTS (
    RUN_ID          VARCHAR         NOT NULL,
    AGENT_NAME      VARCHAR         NOT NULL DEFAULT 'openai',
    MODEL_NAME      VARCHAR         NOT NULL,
    QUESTION        VARCHAR         NOT NULL,
    AGENT_RESPONSE  VARCHAR         NOT NULL,
    SCORE           FLOAT           NOT NULL,
    REASONING       VARCHAR         NOT NULL,
    PASS            BOOLEAN         NOT NULL,
    RUBRIC_ID       VARCHAR         NOT NULL,
    RUN_TIMESTAMP   TIMESTAMP_NTZ   NOT NULL
)
"""


def _ensure_table() -> None:
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(_CREATE_TABLE_SQL)


def _write_result(run_id: str, agent_name: str, model_name: str, run_ts: datetime,
                  question: str, agent_response: str, score_result: dict, rubric_id: str) -> None:
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(_WRITE_SQL, (
            run_id,
            agent_name,
            model_name,
            question,
            agent_response,
            score_result["score"],
            score_result["reasoning"],
            score_result["pass"],
            rubric_id,
            run_ts,
        ))


def run_evaluation(limit: int | None = None, agent_name: str | None = None) -> dict:
    """Run the full golden suite for one agent. Returns summary metrics."""
    _ensure_table()

    name = agent_name or os.getenv("AGENT_NAME", DEFAULT_AGENT)
    if name not in AGENT_REGISTRY:
        raise ValueError(f"Unknown agent: {name!r}. Available: {list(AGENT_REGISTRY)}")
    model = get_model_name(name)

    run_id = str(uuid.uuid4())
    run_ts = datetime.now(timezone.utc)
    logger.info("Starting eval run %s — agent=%s at %s", run_id, name, run_ts.isoformat())

    suite = load_golden_suite()
    if limit:
        suite = suite[:limit]

    scores: list[float] = []
    passes: list[bool] = []

    for i, case in enumerate(suite, 1):
        question = case["question"]
        rubric_id = case["rubric_id"]
        logger.info("[%d/%d] agent=%s | %s", i, len(suite), name, question)

        agent_response = run_agent_on_question(question, name)
        result = score_response(question, agent_response, rubric_id)

        _write_result(run_id, name, model, run_ts, question, agent_response, result, rubric_id)
        scores.append(result["score"])
        passes.append(result["pass"])
        if i < len(suite):
            time.sleep(4)

    pass_rate = sum(passes) / len(passes) if passes else 0.0
    avg_score = sum(scores) / len(scores) if scores else 0.0
    sorted_scores = sorted(scores)
    p90_idx = int(len(sorted_scores) * 0.9) - 1
    p90_score = sorted_scores[max(p90_idx, 0)] if sorted_scores else 0.0

    score_threshold = float(os.getenv("EVAL_SCORE_THRESHOLD", "0.75"))
    pass_rate_threshold = float(os.getenv("EVAL_PASS_RATE_THRESHOLD", "0.85"))

    summary = {
        "run_id": run_id,
        "agent_name": name,
        "total": len(suite),
        "pass_count": sum(passes),
        "fail_count": len(passes) - sum(passes),
        "pass_rate": round(pass_rate, 4),
        "avg_score": round(avg_score, 4),
        "p90_score": round(p90_score, 4),
        "passed": p90_score >= score_threshold and pass_rate >= pass_rate_threshold,
    }

    logger.info("run %s (%s) done — pass_rate=%.2f passed=%s",
                run_id, name, pass_rate, summary["passed"])
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None,
                        help="Limit to first N golden questions (smoke test)")
    parser.add_argument("--agent", type=str, default=None,
                        help=f"Agent to evaluate (default: AGENT_NAME env var or '{DEFAULT_AGENT}'). "
                             f"Available: {list(AGENT_REGISTRY)}")
    args = parser.parse_args()

    summary = run_evaluation(limit=args.limit, agent_name=args.agent)
    print("\neval results:")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    exit(0 if summary["passed"] else 1)
