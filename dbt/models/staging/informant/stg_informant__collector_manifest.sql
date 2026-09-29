select
    path as file_path,
    fetched_at,
    rows as row_count,
    sha256
from {{ source('informant', 'collector_manifest') }}
