#!/usr/bin/env python3
"""load_csv.py — Workstream C

dlt-Ingestion: lädt den CSV File-Export (Input Port) in eine DuckDB raw-Tabelle.
Materialisiert den Input Port; dbt transformiert anschließend raw -> mart.

Aufruf:
    python pipeline/ingest/load_csv.py --source data/sample_radverkehr_tageswerte_2025_01.csv \\
        --duckdb pipeline/dbt/warehouse.duckdb --table raw_radverkehr_tage
"""
from __future__ import annotations
import argparse
import sys

# TODO(Workstream C): mit dlt umsetzen, z.B.
#   import dlt
#   pipeline = dlt.pipeline(pipeline_name="radverkehr", destination="duckdb",
#                           dataset_name="raw")
#   pipeline.run(read_csv_rows(args.source), table_name=args.table)
# Hinweis: Spalte 'min-temp'/'max-temp' enthalten '-' -> beim Laden roh belassen,
# Bereinigung (Komma->Punkt, Cast) passiert in dbt staging.


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="dlt: CSV -> DuckDB raw")
    ap.add_argument("--source", default="data/sample_radverkehr_tageswerte_2025_01.csv")
    ap.add_argument("--duckdb", default="pipeline/dbt/warehouse.duckdb")
    ap.add_argument("--table", default="raw_radverkehr_tage")
    args = ap.parse_args(argv)
    sys.stderr.write(f"[stub] load_csv.py: {args.source} -> {args.duckdb}:{args.table} — TODO Workstream C\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
