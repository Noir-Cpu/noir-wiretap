-- When each source was last loaded and how many rows the warehouse holds.
select 'GitHub: workflow runs' as source, count(*) as row_count, max(created_at) as latest_event_at from marts.fct_workflow_run
union all
select 'GitHub: commits', count(*), max(committed_at) from marts.fct_commit
union all
select 'GitHub: pull requests', count(*), max(created_at) from marts.fct_pull_request
union all
select 'INFORMANT: matches', count(*), max(cast(date_key as timestamp)) from marts.fct_match
