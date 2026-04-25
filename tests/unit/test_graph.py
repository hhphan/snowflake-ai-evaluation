from unittest.mock import patch


@patch("src.agent.tools.execute_query")
def test_query_returns_list(mock_exec):
    from src.agent.tools import query_customer_context

    mock_exec.return_value = [{"ORDER_KEY": 1, "ORDER_STATUS": "O"}]
    result = query_customer_context.invoke({"order_id": 1})
    assert isinstance(result, list)


@patch("src.agent.tools.execute_query")
def test_query_not_found(mock_exec):
    from src.agent.tools import query_customer_context

    mock_exec.return_value = []
    result = query_customer_context.invoke({"order_id": 99999999})
    assert result == []
