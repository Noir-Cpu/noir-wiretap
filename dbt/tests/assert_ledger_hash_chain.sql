-- Every ledger record must point at the hash of the record before it (seq order). Zero rows pass.
select prediction_id, ledger_seq
from (
    select prediction_id, ledger_seq, prev_hash,
           lag(prediction_id) over (order by ledger_seq) as expected_prev
    from {{ ref('stg_informant__predictions') }}
)
where prev_hash is distinct from expected_prev
