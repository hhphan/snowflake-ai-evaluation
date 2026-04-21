with source as (
    select * from {{ source('tpch', 'orders') }}
)

select
    o_orderkey       as order_key,
    o_custkey        as customer_key,
    o_orderstatus    as status,
    o_totalprice     as total_price,
    o_orderdate      as order_date,
    o_orderpriority  as priority,
    o_clerk          as clerk,
    o_shippriority   as ship_priority,
    o_comment        as comment
from source
