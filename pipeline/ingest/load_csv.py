#!/usr/bin/env python3
"""load_csv.py — Workstream C

dlt-Ingestion: lädt den CSV File-Export (Input Port) in eine DuckDB raw-Tabelle.
Materialisiert den Input Port; dbt transformiert anschließend raw -> mart.

Die Rohdaten werden bewusst UNVERÄNDERT geladen (alle Spalten als Text), damit
die Quelle 1:1 abgebildet wird. Bereinigung (Komma->Punkt, Casts, datum->DATE,
Spalten-Rename 'min-temp'->'min_temp') passiert erst im dbt-Staging.

Aufruf:
    python pipeline/ingest/load_csv.py --source data/sample_radverkehr_tageswerte_2025_01.csv \\
        --duckdb pipeline/dbt/warehouse.duckdb --table raw_radverkehr_tage
"""
from __future__ import annotations
import argparse
import csv
import sys
from pathlib import Path

import dlt


def read_csv_rows(source: str):
    """Liest die CSV zeilenweise als dicts (alle Werte roh als str).

    Spaltennamen bleiben exakt wie in der Quelle (inkl. 'min-temp'/'max-temp'
    mit Bindestrich) — das Staging übernimmt das Umbenennen/Casten.
    """
    with open(source, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            # Werte roh als String belassen; leere Felder -> None
            yield {k: (v if v != "" else None) for k, v in row.items()}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="dlt: CSV -> DuckDB raw")
    ap.add_argument("--source", default="data/sample_radverkehr_tageswerte_2025_01.csv")
    ap.add_argument("--duckdb", default="pipeline/dbt/warehouse.duckdb")
    ap.add_argument("--table", default="raw_radverkehr_tage")
    ap.add_argument("--schema", default="raw", help="DuckDB-Schema (dlt dataset_name)")
    args = ap.parse_args(argv)

    src = Path(args.source)
    if not src.exists():
        sys.stderr.write(f"[load_csv] Quelle nicht gefunden: {src}\n")
        return 2

    # DuckDB-Zielpfad an dlt übergeben; Verzeichnis sicherstellen.
    duckdb_path = Path(args.duckdb)
    duckdb_path.parent.mkdir(parents=True, exist_ok=True)

    pipeline = dlt.pipeline(
        pipeline_name="radverkehr",
        destination=dlt.destinations.duckdb(str(duckdb_path)),
        dataset_name=args.schema,
    )

    # write_disposition="replace": idempotent — jeder Lauf ersetzt die raw-Tabelle,
    # damit die Pipeline (auch im CI) reproduzierbar dieselben Daten materialisiert.
    info = pipeline.run(
        read_csv_rows(str(src)),
        table_name=args.table,
        write_disposition="replace",
    )

    rows = sum(1 for _ in read_csv_rows(str(src)))
    sys.stderr.write(
        f"[load_csv] {rows} Zeilen geladen: {src} -> {duckdb_path}:{args.schema}.{args.table}\n"
    )
    # dlt loggt Paket-Details; bei Bedarf zur Diagnose ausgeben.
    print(info)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
