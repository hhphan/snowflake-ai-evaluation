with order_details as (
    select * from {{ ref('int_order_details') }}
),

customers as (
    select * from {{ ref('stg_tpch__customers') }}
),

customer_summary as (
    select * from {{ ref('int_customer_order_summary') }}
)

select
    od.order_key,
    od.customer_key,
    c.name                          as customer_name,
    c.phone                         as customer_phone,
    c.account_balance               as customer_account_balance,
    c.market_segment,

    od.order_status,
    od.order_date,
    od.order_total_price,
    od.order_priority,

    od.line_number,
    od.part_key,
    od.part_name,
    od.part_brand,
    od.part_type,
    od.quantity,
    od.extended_price,
    od.discount,
    od.net_price,
    od.return_flag,
    od.line_status,
    od.ship_date,
    od.commit_date,
    od.receipt_date,
    od.ship_mode,
    od.ship_instructions,
    od.transit_days,

    cs.total_orders                 as customer_total_orders,
    cs.total_spend                  as customer_total_spend,
    cs.avg_order_value              as customer_avg_order_value,
    cs.first_order_date             as customer_first_order_date,
    cs.latest_order_date            as customer_latest_order_date,
    cs.open_orders                  as customer_open_orders,
    cs.fulfilled_orders             as customer_fulfilled_orders
from order_details od
inner join customers       c  on od.customer_key = c.customer_key
inner join customer_summary cs on od.order_key = cs.customer_key
