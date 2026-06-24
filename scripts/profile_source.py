#!/usr/bin/env python3
"""profile_source.py — Workstream A

Schritt 1 der Post-Freigabe-Pipeline. Liest die CSV aus source.location und
erzeugt profiling.json: Spalten/Typen/Nullable, Kandidaten-Quality-Regeln,
PII-Verdacht, Freshness. Ausgabe wird von intake_to_odcs.py mit den
Governance-Feldern aus intake.json zum finalen ODCS-Contract gemergt.

Bewusst ohne externe Abhängigkeiten (nur stdlib) — läuft lokal überall ohne
Install-Schritt.

Aufruf:
    python scripts/profile_source.py --source data/sample_radverkehr_tageswerte_2025_01.csv [--out profiling.json]
"""
from __future__ import annotations
import argparse
import csv
import json
import re
import sys

PII_HINTS = ("name", "vorname", "nachname", "adresse", "strasse", "geburt", "email", "telefon", "personen")

# Datum YYYY.MM.DD (LHM-opendata-Konvention) bzw. ISO YYYY-MM-DD.
_DATE_RE = re.compile(r"^\d{4}[.\-/]\d{2}[.\-/]\d{2}$")
# Uhrzeit HH:MM(:SS) — verlangt ':' als Trenner, damit '23.59' nicht fälschlich
# als Zeit (statt Dezimalzahl) erkannt wird (echtes Quell-Qualitätssignal).
_TIME_RE = re.compile(r"^\d{1,2}:\d{2}(?::\d{2})?$")
_INT_RE = re.compile(r"^[+-]?\d+$")
_FLOAT_RE = re.compile(r"^[+-]?(\d+([.,]\d*)?|[.,]\d+)$")


def _is_empty(v) -> bool:
    return v is None or v.strip() == ""


def _to_float(v: str) -> float:
    return float(v.replace(",", "."))


def _infer_type(values: list[str]) -> str:
    """Logischer ODCS-Typ aus nicht-leeren Werten. Reihenfolge = strikt -> lax."""
    if not values:
        return "string"
    if all(_INT_RE.match(v) for v in values):
        return "integer"
    if all(_FLOAT_RE.match(v) for v in values):
        return "number"
    if all(_DATE_RE.match(v) for v in values):
        return "date"
    if all(_TIME_RE.match(v) for v in values):
        return "time"
    return "string"


# logischer Typ -> Vorschlag physischer Typ (DuckDB/Postgres-nah, fuer den Draft).
_PHYSICAL = {
    "integer": "INTEGER",
    "number": "DOUBLE",
    "date": "DATE",
    "time": "TIME",
    "string": "VARCHAR",
}


def _column_stats(name: str, values: list[str], row_count: int) -> dict:
    present = [v for v in values if not _is_empty(v)]
    null_rate = round(1 - len(present) / row_count, 4) if row_count else 0.0
    distinct = len(set(present))
    unique_rate = round(distinct / len(present), 4) if present else 0.0
    logical = _infer_type(present)

    col: dict = {
        "name": name,
        "logical_type": logical,
        "physical_type": _PHYSICAL[logical],
        "null_rate": null_rate,
        "unique_rate": unique_rate,
        "min": None,
        "max": None,
    }

    if logical in ("integer", "number") and present:
        nums = [_to_float(v) for v in present]
        lo, hi = min(nums), max(nums)
        cast = int if logical == "integer" else float
        col["min"], col["max"] = cast(lo), cast(hi)
    elif logical == "date" and present:
        # Normalisierte Sortierung: YYYY?MM?DD ist lexikografisch = chronologisch.
        norm = sorted(v.replace("/", "-").replace(".", "-") for v in present)
        col["min"], col["max"] = norm[0], norm[-1]

    return col


def _detect_sum_expressions(header: list[str], rows: list[list[str]], numeric_cols: list[str]) -> list[dict]:
    """Findet Spalten c mit c == a + b ueber alle Zeilen (z.B. gesamt = richtung_1 + richtung_2)."""
    idx = {name: header.index(name) for name in numeric_cols}
    found = []
    for c in numeric_cols:
        for i, a in enumerate(numeric_cols):
            for b in numeric_cols[i + 1:]:
                if c in (a, b):
                    continue
                ok = checked = 0
                for r in rows:
                    va, vb, vc = r[idx[a]], r[idx[b]], r[idx[c]]
                    if any(_is_empty(x) for x in (va, vb, vc)):
                        continue
                    checked += 1
                    if abs(_to_float(va) + _to_float(vb) - _to_float(vc)) < 1e-6:
                        ok += 1
                if checked and ok == checked:
                    found.append({"rule": "expression", "expr": f"{c} = {a} + {b}"})
    return found


def profile_csv(path: str) -> dict:
    """CSV -> profiling-dict (Spalten, Kandidaten-Quality, PII-Verdacht, Freshness)."""
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        rows = [r for r in reader if any(not _is_empty(c) for c in r)]

    row_count = len(rows)
    by_col = {name: [r[i] if i < len(r) else "" for r in rows] for i, name in enumerate(header)}

    columns = [_column_stats(name, by_col[name], row_count) for name in header]

    # --- Kandidaten-Quality-Regeln ---
    quality_rules: list[dict] = []
    for col in columns:
        name = col["name"]
        if col["null_rate"] == 0.0 and row_count:
            quality_rules.append({"rule": "not_null", "column": name})
        if col["unique_rate"] == 1.0 and row_count > 1:
            quality_rules.append({"rule": "unique", "column": name})
        if col["logical_type"] in ("integer", "number") and col["min"] is not None:
            quality_rules.append({"rule": "range", "column": name, "min": col["min"], "max": col["max"]})

    numeric_cols = [c["name"] for c in columns if c["logical_type"] in ("integer", "number")]
    quality_rules.extend(_detect_sum_expressions(header, rows, numeric_cols))

    # --- PII-Verdacht (Heuristik ueber Spaltennamen) ---
    pii_suspect = [c["name"] for c in columns if any(h in c["name"].lower() for h in PII_HINTS)]

    # --- Freshness: juengstes Datum der ersten Datumsspalte ---
    freshness = {}
    for col in columns:
        if col["logical_type"] == "date" and col["max"] is not None:
            freshness = {"column": col["name"], "max": col["max"]}
            break

    return {
        "source": path,
        "row_count": row_count,
        "columns": columns,
        "quality_rules": quality_rules,
        "pii_suspect": pii_suspect,
        "freshness": freshness,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Profiler (Pipeline-Schritt 1): Quelle -> profiling.json")
    ap.add_argument("--source", required=True, help="Pfad zur Quelle (CSV im Demo)")
    ap.add_argument("--out", default="-", help="Zieldatei oder '-' für stdout")
    args = ap.parse_args(argv)

    try:
        result = profile_csv(args.source)
    except FileNotFoundError:
        sys.stderr.write(f"Quelle nicht gefunden: {args.source}\n")
        return 2

    out = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out == "-":
        print(out)
    else:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(out)
        sys.stderr.write(f"profiling -> {args.out} ({result['row_count']} Zeilen, {len(result['columns'])} Spalten)\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
