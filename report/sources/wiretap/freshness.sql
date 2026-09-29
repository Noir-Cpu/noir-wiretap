select
    (select max(fetched_at) from staging.stg_informant__collector_manifest) as informant_collector_fetched_at,
    (select max(loaded_at) from staging.stg_github__repos) as github_loaded_at
