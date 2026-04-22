with orders as (
    select * from {{ ref('stg_tpch__orders') }}
),

lineitems as (
    select * from {{ ref('stg_tpch__lineitems') }}
),

parts as (
    select * from {{ ref('stg_tpch__parts') }}
)

select
    o.order_key,
    o.customer_key,
    o.status                                              as order_status,
    o.order_date,
    o.total_price                                         as order_total_price,
    o.priority                                            as order_priority,
    l.line_number,
    l.part_key,
    p.name                                                as part_name,
    p.brand                                               as part_brand,
    p.type                                                as part_type,
    l.quantity,
    l.extended_price,
    l.discount,
    round(l.extended_price * (1 - l.discount), 2)        as net_price,
    l.return_flag,
    l.line_status,
    l.ship_date,
    l.commit_date,
    l.receipt_date,
    l.ship_mode,
    l.ship_instructions,
    datediff('day', l.ship_date, l.receipt_date)         as transit_days
from orders o
inner join lineitems l on o.order_key = l.order_id
inner join parts     p on l.part_key  = p.part_key
