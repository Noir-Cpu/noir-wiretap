---
title: WIRETAP
---

# CASE 004 / WIRETAP

A small warehouse that listens in on the NOIR systems. Loaded by dlt, modelled in dbt on DuckDB, reported here from the marts. Every number on this site is a column in a dbt mart; no page recomputes a metric.

```sql freshness
select * from wiretap.freshness
```

```sql status
select * from wiretap.run_status
```

<BigValue data={freshness} value=github_loaded_at title="GitHub last loaded (UTC)" fmt="yyyy-mm-dd hh:mm" />
<BigValue data={freshness} value=informant_collector_fetched_at title="INFORMANT collector last fetched (UTC)" fmt="yyyy-mm-dd hh:mm" />

## What is in the warehouse

<DataTable data={status}>
  <Column id=source />
  <Column id=row_count title="Rows" fmt="#,##0" />
  <Column id=latest_event_at title="Latest event" fmt="yyyy-mm-dd hh:mm" />
</DataTable>

## Analyses

- [Home advantage: Premier League against La Liga](/analyses/home-advantage)
- [Delivery cadence and CI reliability across the NOIR repos](/analyses/delivery-and-ci)
- [How well calibrated is INFORMANT?](/analyses/calibration)
- [Sources, limits and what is deliberately left out](/about)
