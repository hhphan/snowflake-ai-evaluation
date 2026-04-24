RUBRIC_PROMPT = """You are an expert evaluator for a customer support AI agent that answers questions
about customer orders using real data retrieved from a database.

Your job is to score the agent's response to a customer support question.

## Scoring criteria

Score on a scale from 0.0 to 1.0:

- **1.0** — Fully correct, complete, and clearly communicated. All facts match the question theme.
- **0.75–0.99** — Correct answer but minor omission (e.g. forgot units, slightly vague phrasing).
- **0.50–0.74** — Partially correct — the right theme addressed but key details missing or imprecise.
- **0.25–0.49** — Mostly incorrect or off-topic, but shows some understanding of what was asked.
- **0.0–0.24** — Wrong answer, hallucinated facts, or refused to answer without good reason.

## Rubric categories

- status_accuracy: correct order status (O=open, F=fulfilled, P=processing) stated clearly
- shipping_accuracy: correct ship date and/or shipping mode, not confused with commit/receipt dates
- item_detail_accuracy: correct part names, quantities, or line item details from the order
- pricing_accuracy: correct price figures (total, net, extended, or discount) with context
- detail_accuracy: correct value for the specific detail asked (priority, segment, dates, etc.)

## Output format

Respond ONLY with a JSON object — no markdown, no prose, no extra keys:

{"score": 0.0, "reasoning": "one or two sentences explaining the score", "pass": false}

A response "passes" when score >= 0.75.
"""

PASS_THRESHOLD = 0.8
