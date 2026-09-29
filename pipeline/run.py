"""Extract and load: GitHub + INFORMANT into DuckDB (raw_* schemas). Run: python -m pipeline.run"""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

import dlt

from .github_source import github_source
from .informant_source import informant_source

DB_PATH = Path(os.environ.get("WIRETAP_DB", Path(__file__).resolve().parents[1] / "warehouse" / "wiretap.duckdb"))


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    for name, source in (("raw_github", github_source()), ("raw_informant", informant_source())):
        pipeline = dlt.pipeline(
            pipeline_name=name,
            destination=dlt.destinations.duckdb(str(DB_PATH)),
            dataset_name=name,
            pipelines_dir=str(DB_PATH.parent / ".dlt_pipelines"),
        )
        info = pipeline.run(source)
        print(info)
        info.raise_on_failed_jobs()
    return 0


if __name__ == "__main__":
    sys.exit(main())
