from langchain_core.tools import tool
from src.utils.snowflake_client import execute_query


@tool
def query_customer_context(order_id: int) -> list[dict]:
    """Retrieve full order and customer details for a given order ID.

    Returns one row per line item in the order, enriched with customer profile
    and lifetime order statistics. Returns an empty list if the order is not found.
    """
    return execute_query(
        "SELECT * FROM ANALYTICS_DB.MARTS.MART_CUSTOMER_SUPPORT_CONTEXT WHERE order_key = %s",
        (order_id,),
    )
