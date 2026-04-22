with orders as (
    select * from {{ ref('stg_tpch__orders') }}
)

select
    customer_key,
    count(*)                    as total_orders,
    sum(total_price)            as total_spend,
    avg(total_price)            as avg_order_value,
    min(order_date)             as first_order_date,
    max(order_date)             as latest_order_date,
    sum(case when status = 'O' then 1 else 0 end) as open_orders,
    sum(case when status = 'F' then 1 else 0 end) as fulfilled_orders
from orders
group by customer_key
