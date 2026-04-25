from unittest.mock import patch


@patch("src.evaluation.golden_suite.execute_query")
def test_load_returns_questions(mock_exec):
    from src.evaluation.golden_suite import load_golden_suite

    mock_exec.return_value = [
        {"QUESTION": "What is order 1?", "EXPECTED_THEME": "order_status", "RUBRIC_ID": "status_accuracy"}
    ]
    suite = load_golden_suite()
    assert len(suite) == 1
    assert suite[0]["question"] == "What is order 1?"
