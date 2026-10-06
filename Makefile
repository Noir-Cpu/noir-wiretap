PY := .venv/bin/python
DBT := cd dbt && ../.venv/bin/dbt

.PHONY: setup run extract freshness build test site deploy findings clean

# One command, from a clean checkout: venv, deps, extract/load, freshness gate, dbt build (seed, snapshot, models, tests).
run: setup extract freshness build

setup: .venv/.installed report/node_modules/.installed

.venv/.installed: requirements.txt
	python3 -m venv .venv
	.venv/bin/pip install -q --upgrade pip
	.venv/bin/pip install -q -r requirements.txt
	touch $@

report/node_modules/.installed: report/package.json report/package-lock.json
	cd report && npm ci
	touch $@

extract:
	$(PY) -m pipeline.run

# Fails when a source is older than its threshold (see dbt/models/staging/_sources.yml).
freshness:
	$(DBT) source freshness --profiles-dir .

build:
	$(DBT) build --profiles-dir .

test:
	.venv/bin/pytest -q

# site/ = lightweight static pages at / plus the interactive Evidence report at /explore (ADR 0009).
site: report/node_modules/.installed
	rm -rf report/build
	cd report && npm run sources && npm run build:strict
	node scripts/externalize_wasm.mjs
	node scripts/postprocess_explore.mjs
	rm -rf site && mkdir -p site
	cp -r report/build site/explore
	.venv/bin/python scripts/build_static.py
	.venv/bin/python scripts/build_headers.py

deploy: site
	npx wrangler deploy

findings:
	$(PY) scripts/findings.py

clean:
	rm -r warehouse/wiretap.duckdb dbt/target report/build
