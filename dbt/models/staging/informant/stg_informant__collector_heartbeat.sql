select cast(checked_at as timestamptz) as checked_at
from {{ source('informant', 'collector_heartbeat') }}
