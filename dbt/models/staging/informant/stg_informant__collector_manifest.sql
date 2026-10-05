select
    path as file_path,
    fetched_at as last_data_change_at,
    rows as row_count,
    sha256
from {{ source('informant', 'collector_manifest') }}
