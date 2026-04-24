-- Fails if any completed eval run has null scores — indicates a broken scorer.
select *
from {{ source('evaluation', 'eval_results') }}
where score is null
   or reasoning is null
   or pass is null
