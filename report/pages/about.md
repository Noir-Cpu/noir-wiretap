---
title: Sources, limits and exclusions
---

# Sources, limits and exclusions

| Source | Status | Notes |
| --- | --- | --- |
| GitHub REST API, Noir-Cpu `noir-*` repos | Live | Repos, commits, workflow runs, pull requests, releases. Author names and emails are not extracted. |
| INFORMANT results (E0, SP1) | Live | Read from the public noir-informant repo. Results and match statistics only, no odds, no predictions. |
| INFORMANT predictions | Reserved | Source declared, format not defined. See ADR 0005. |
| DISPATCH order events | Not built | The source does not exist yet. Contract in ADR 0004. |
| WITNESS turnout | Not built | Aggregates only, guarded by a dbt test. Ballots and participation never enter the warehouse. See ADR 0003. |

The warehouse is rebuilt nightly by GitHub Actions and this site is published from that build.
