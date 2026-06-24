#!/usr/bin/env python3
"""export_output_port.py — Workstream C

Schreibt den Output Port (dbt-Mart-View) zusätzlich als Datei-Export
(Parquet + CSV) unter output/. Das ist der zweite Serving-Kanal des
Output Ports neben der DB-View — für Batch-/FME-/Laufwerks-Konsumenten
(siehe docs/access-and-output-port.md, serving: file_export).

Der Zielpfad steht im data-product.yaml (ports.output[].serving) bzw. im
Contract-servers[]. Hier: Repo-relativ output/ (gitignored).

Aufruf:
    python pipeline/export_output_port.py --duckdb pipeline/dbt/warehouse.duckdb \\
        --object radverkehr_tageswerte --out-dir output
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

import duckdb


def export(duckdb_path: str, obj: str, out_dir: str) -> list[Path]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    parquet = out / f"{obj}.parquet"
    csv = out / f"{obj}.csv"

    con = duckdb.connect(duckdb_path, read_only=True)
    try:
        ident = '"' + obj.replace('"', '""') + '"'
        # Stabile Sortierung -> reproduzierbarer Export (PK datum, zaehlstelle).
        select = f"SELECT * FROM {ident} ORDER BY datum, zaehlstelle"
        con.execute(f"COPY ({select}) TO '{parquet.as_posix()}' (FORMAT PARQUET)")
        con.execute(f"COPY ({select}) TO '{csv.as_posix()}' (HEADER, DELIMITER ',')")
        rows = con.execute(f"SELECT count(*) FROM {ident}").fetchone()[0]
    finally:
        con.close()

    sys.stderr.write(f"[export] {rows} Zeile(n) -> {parquet}, {csv}\n")
    return [parquet, csv]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Output Port als Parquet/CSV exportieren")
    ap.add_argument("--duckdb", default="pipeline/dbt/warehouse.duckdb")
    ap.add_argument("--object", default="radverkehr_tageswerte", help="View/Tabelle (Output Port)")
    ap.add_argument("--out-dir", default="output")
    args = ap.parse_args(argv)

    if not Path(args.duckdb).exists():
        sys.stderr.write(f"[export] Warehouse nicht gefunden: {args.duckdb} — erst Pipeline bauen.\n")
        return 2

    export(args.duckdb, args.object, args.out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
