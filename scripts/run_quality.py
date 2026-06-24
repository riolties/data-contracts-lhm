#!/usr/bin/env python3
"""run_quality.py — Workstream C

Führt die im Contract deklarierten quality-Regeln gegen die MATERIALISIERTEN
Daten (DuckDB) aus. Ergänzend laufen dbt-Tests (pipeline/dbt). Exit != 0 bei
Verstoß gegen eine Regel mit severity=error (warning blockt nicht).

Quality-Konvention (siehe docs/architecture.md & die *.odcs.yaml):
Jede Regel liegt unter schema[].quality[] als ODCS-Typ 'text'; die ausführbare
Logik steht in customProperties (property/value) mit einem 'engine'-Feld:
  engine=sql           -> 'query' ausführen, Skalar-Ergebnis muss 'expect' sein
  engine=range         -> Werte in 'column' außerhalb [min, max] zählen (=0)
  engine=unique        -> 'columns' bilden eindeutigen Schlüssel (keine Duplikate)
  engine=not_null      -> 'column' hat keine NULLs
  engine=row_count_min -> Tabelle hat >= 'min' Zeilen

Aufruf:
    python scripts/run_quality.py --contract <output.odcs.yaml> \\
        --duckdb pipeline/dbt/warehouse.duckdb --table radverkehr_tageswerte
"""
from __future__ import annotations
import argparse
import sys

import duckdb
import yaml


def _props(rule: dict) -> dict:
    """customProperties-Liste -> dict {property: value}."""
    return {cp["property"]: cp["value"] for cp in rule.get("customProperties", [])}


def _num(v):
    """YAML kann Zahlen als int/str liefern — robust zu Zahl casten."""
    if isinstance(v, bool):
        return v
    try:
        f = float(v)
        return int(f) if f.is_integer() else f
    except (TypeError, ValueError):
        return v


def _ident(name: str) -> str:
    """Spalten-/Tabellenname als DuckDB-Identifier quoten (Schutz vor Sonderzeichen)."""
    return '"' + str(name).replace('"', '""') + '"'


def collect_rules(contract: dict) -> list[dict]:
    """Alle quality-Regeln über alle schema[]-Einträge einsammeln."""
    rules = []
    for entry in contract.get("schema", []):
        rules.extend(entry.get("quality", []))
    return rules


def run_rule(rule: dict, con, table: str) -> tuple[bool, str]:
    """Eine Regel ausführen. Liefert (passed, detail-Text)."""
    p = _props(rule)
    engine = p.get("engine")
    tbl = _ident(table)

    if engine == "sql":
        query = p["query"]
        expect = _num(p.get("expect", 0))
        observed = con.execute(query).fetchone()[0]
        passed = _num(observed) == expect
        return passed, f"erwartet={expect}, beobachtet={observed}"

    if engine == "range":
        col = _ident(p["column"])
        mn, mx = _num(p["min"]), _num(p["max"])
        q = f"SELECT count(*) FROM {tbl} WHERE {col} < {mn} OR {col} > {mx}"
        observed = con.execute(q).fetchone()[0]
        return observed == 0, f"{observed} Wert(e) außerhalb [{mn}, {mx}]"

    if engine == "unique":
        cols = p["columns"]
        if isinstance(cols, str):
            cols = [c.strip() for c in cols.split(",")]
        collist = ", ".join(_ident(c) for c in cols)
        q = (
            f"SELECT count(*) FROM (SELECT {collist} FROM {tbl} "
            f"GROUP BY {collist} HAVING count(*) > 1)"
        )
        observed = con.execute(q).fetchone()[0]
        return observed == 0, f"{observed} doppelte(r) Schlüssel ({', '.join(cols)})"

    if engine == "not_null":
        col = _ident(p["column"])
        q = f"SELECT count(*) FROM {tbl} WHERE {col} IS NULL"
        observed = con.execute(q).fetchone()[0]
        return observed == 0, f"{observed} NULL-Wert(e) in {p['column']}"

    if engine == "row_count_min":
        mn = _num(p["min"])
        observed = con.execute(f"SELECT count(*) FROM {tbl}").fetchone()[0]
        return observed >= mn, f"{observed} Zeile(n) (min {mn})"

    return False, f"unbekannte engine '{engine}'"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Data-Quality-Gate gegen materialisierte Daten")
    ap.add_argument("--contract", required=True)
    ap.add_argument("--duckdb", default="pipeline/dbt/warehouse.duckdb")
    ap.add_argument("--table", required=True)
    args = ap.parse_args(argv)

    with open(args.contract, encoding="utf-8") as fh:
        contract = yaml.safe_load(fh)

    rules = collect_rules(contract)
    if not rules:
        sys.stderr.write(f"[run_quality] keine quality-Regeln in {args.contract}\n")
        return 0

    con = duckdb.connect(args.duckdb, read_only=True)

    errors = 0
    warnings = 0
    print(f"Quality Gate: {len(rules)} Regel(n) gegen '{args.table}'")
    for rule in rules:
        name = rule.get("name", "<unbenannt>")
        severity = (rule.get("severity") or "error").lower()
        try:
            passed, detail = run_rule(rule, con, args.table)
        except Exception as exc:  # Regel-Fehler = Verstoß (defensiv)
            passed, detail = False, f"Ausführungsfehler: {exc}"

        if passed:
            status = "PASS"
        elif severity == "warning":
            status = "WARN"
            warnings += 1
        else:
            status = "FAIL"
            errors += 1
        print(f"  [{status}] {name} ({severity}) — {detail}")

    con.close()

    print(f"\nErgebnis: {errors} Fehler, {warnings} Warnung(en).")
    if errors:
        sys.stderr.write("[run_quality] Quality Gate FEHLGESCHLAGEN (severity=error)\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
