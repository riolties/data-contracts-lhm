#!/usr/bin/env python3
"""profile_source.py — Workstream A

Schritt 1 der Post-Freigabe-Pipeline. Liest die CSV aus source.location und
erzeugt profiling.json: Spalten/Typen/Nullable, Kandidaten-Quality-Regeln,
PII-Verdacht, Freshness. Ausgabe wird von intake_to_odcs.py mit den
Governance-Feldern aus intake.json zum finalen ODCS-Contract gemergt.

Aufruf:
    python scripts/profile_source.py --source data/sample_radverkehr_tageswerte_2025_01.csv [--out profiling.json]
"""
from __future__ import annotations
import argparse
import json
import sys

PII_HINTS = ("name", "vorname", "nachname", "adresse", "strasse", "geburt", "email", "telefon", "personen")


def profile_csv(path: str) -> dict:
    """CSV -> profiling-dict. TODO(Workstream A): mit pandas implementieren.

    Erwartet u.a.:
      - columns: [{name, logical_type, physical_type, null_rate, unique_rate, min, max}]
      - candidate_quality: [{rule: not_null|unique|range|expression, column?, min?, max?, expr?}]
      - pii_suspect: [<spaltenname>]   (Heuristik via PII_HINTS)
      - freshness: {column, max}
      - row_count: int
    """
    raise NotImplementedError("profile_csv: Workstream A")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Profiler: Quelle -> Draft (profiling.json)")
    ap.add_argument("--source", required=True, help="Pfad zur Quelle (CSV im Demo)")
    ap.add_argument("--out", default="-", help="Zieldatei oder '-' für stdout")
    args = ap.parse_args(argv)

    # TODO(Workstream A): result = profile_csv(args.source)
    sys.stderr.write("[stub] profile_source.py noch nicht implementiert (Workstream A)\n")
    result = {"columns": [], "candidate_quality": [], "pii_suspect": [], "freshness": {}, "row_count": 0}

    out = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out == "-":
        print(out)
    else:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
