---
title: Calibration of INFORMANT predictions
---

# How well calibrated is INFORMANT?

```sql status
select * from wiretap.calibration_status
```

```sql cal
select * from wiretap.calibration
```

```sql bins
select * from wiretap.calibration_bins
```

{#if status[0].scored < 30}

**Not enough data yet.** {status[0].scored} scored predictions; no accuracy number is published until there are at least 30.

<DataTable data={status}>
  <Column id=predictions title="In ledger" />
  <Column id=scored title="Scored" />
  <Column id=skipped title="Skipped" />
</DataTable>

{:else}

<DataTable data={cal}>
  <Column id=model_name title="Model" />
  <Column id=scored_predictions title="Scored" />
  <Column id=mean_rps title="Mean RPS" fmt="0.0000" />
  <Column id=mean_log_loss title="Log loss" fmt="0.0000" />
  <Column id=rps_minus_book title="Model minus book (RPS)" fmt="0.0000" />
</DataTable>

<ScatterPlot data={bins} x=mean_predicted y=observed_frequency series=outcome xFmt=pct0 yFmt=pct0 title="Reliability: predicted against observed" />

{/if}

Method and limits: [docs/analyses/03-calibration.md](https://github.com/Noir-Cpu/noir-wiretap/blob/main/docs/analyses/03-calibration.md).
