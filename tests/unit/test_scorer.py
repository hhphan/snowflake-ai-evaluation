import json
from unittest.mock import MagicMock, patch


@patch("src.evaluation.scorer._get_client")
def test_score_pass(mock_get_client):
    from src.evaluation.scorer import score_response

    content = MagicMock()
    content.text = json.dumps({"score": 0.9, "reasoning": "correct", "pass": True})
    resp = MagicMock()
    resp.content = [content]
    resp.usage = MagicMock(input_tokens=10, output_tokens=5)
    mock_get_client.return_value.messages.create.return_value = resp

    result = score_response("What is order 1?", "Order 1 is open.", "status_accuracy")
    assert result["score"] == 0.9
    assert result["pass"] is True


@patch("src.evaluation.scorer._get_client")
def test_invalid_json_fallback(mock_get_client):
    from src.evaluation.scorer import score_response

    content = MagicMock()
    content.text = "oops not json"
    resp = MagicMock()
    resp.content = [content]
    resp.usage = MagicMock(input_tokens=10, output_tokens=5)
    mock_get_client.return_value.messages.create.return_value = resp

    result = score_response("q", "a", "detail_accuracy")
    assert result["score"] == 0.0
    assert result["pass"] is False
