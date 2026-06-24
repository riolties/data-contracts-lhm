#!/usr/bin/env python3
"""run_quality.py — Workstream C

Führt die im Contract deklarierten quality-Regeln gegen die MATERIALISIERTEN
Daten (DuckDB) aus. Ergänzend laufen dbt-Tests (pipeline/dbt). Exit != 0 bei Verstoß.

Aufruf:
    python scripts/run_quality.py --contract <output.odcs.yaml> --duckdb pipeline/dbt/warehouse.duckdb --table radverkehr_tageswerte
"""
from __future__ import annotations
import argparse
import sys


def run_rules(rules: list[dict], con, table: str) -> list[str]:
    """Quality-Regeln gegen DuckDB-Tabelle. Liefert Verstöße (leer = ok).

    TODO(Workstream C): rule-Typen not_null|unique|range|expression als SQL gegen
    `con` ausführen, z.B.:
      not_null   -> SELECT count(*) FROM t WHERE col IS NULL
      range      -> ... WHERE col < min OR col > max
      expression -> ... WHERE NOT (gesamt = richtung_1 + richtung_2)
    """
    raise NotImplementedError("run_rules: Workstream C")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Data-Quality-Gate gegen materialisierte Daten")
    ap.add_argument("--contract", required=True)
    ap.add_argument("--duckdb", default="pipeline/dbt/warehouse.duckdb")
    ap.add_argument("--table", required=True)
    args = ap.parse_args(argv)
    sys.stderr.write(f"[stub] run_quality.py: {args.contract} vs {args.table} — TODO Workstream C\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
