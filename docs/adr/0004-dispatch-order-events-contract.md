# ADR 0004: DISPATCH `order_events` source contract (future source, not built)

Status: proposed. No DISPATCH data exists yet, so nothing is loaded and no fake data is generated. This is what WIRETAP will expect once it does.

Shape: an append-only table `order_events` in DISPATCH's database, exposed to WIRETAP through a read-only role (or a view) limited to these columns.

| Column | Type | Notes |
| --- | --- | --- |
| `event_id` | uuid | Primary key. Loads are idempotent on it. |
| `order_id` | uuid | Groups events of one order. |
| `event_type` | text | `created`, `assigned`, `picked_up`, `delivered`, `failed`, `cancelled`. Unknown values load as-is and fail an accepted-values test rather than being dropped. |
| `occurred_at` | timestamptz | When it happened (UTC). |
| `recorded_at` | timestamptz | When DISPATCH stored it; the dlt incremental cursor. Monotonic per writer. |
| `site_id`, `vehicle_id` | text | Opaque business identifiers. |
| `promised_by` | timestamptz | Set on `created`; needed for on-time delivery. |
| `schema_version` | int | Bumped on breaking changes. |

Not exposed: customer names, phone numbers, addresses, coordinates finer than the site.

Loading: dlt `merge` on `event_id`, incremental on `recorded_at` with a lookback window for late writes. Source freshness: `recorded_at`, warn 12 h, error 26 h.

Planned models: `stg_dispatch__order_events`, `int_dispatch__orders` (one row per order, first and last event times), `fct_order`, `dim_site`, and the metric `on_time_delivery_rate` = delivered orders with `delivered_at <= promised_by` divided by delivered orders, defined once by the same macro pattern as ADR 0002.

Open questions for the DISPATCH side: whether the simulator writes to the same table as real traffic (needs an `is_simulated` flag to keep the metric honest), and who owns the schema version bump.
