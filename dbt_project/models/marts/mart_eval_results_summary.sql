with eval_results as (
    select *
    from {{ source('evaluation', 'eval_results') }}
)

select
    run_id,
    agent_name,
    model_name,
    run_timestamp,
    count(*)                                                     as total_questions,
    sum(case when pass then 1 else 0 end)                        as pass_count,
    sum(case when not pass then 1 else 0 end)                    as fail_count,
    round(sum(case when pass then 1 else 0 end) / count(*), 4)  as pass_rate,
    round(avg(score), 4)                                         as avg_score,
    round(percentile_cont(0.9) within group (order by score), 4) as p90_score
from eval_results
group by run_id, agent_name, model_name, run_timestamp
order by run_timestamp desc
