#!/usr/bin/env python3
"""intake_to_odcs.py — Workstream B

Schritt 2 der Post-Freigabe-Pipeline. Merged den Profiler-Output (profiling.json,
Spalten/Typen/Quality-Kandidaten) mit den Governance-Feldern aus intake.json
(validiert gegen schemas/intake.schema.json) zu einem finalen ODCS-v3-Contract
+ data-product.yaml unter domains/<domain>/data-products/<product>/.

Aufruf:
    python scripts/intake_to_odcs.py --intake intake/intake.example.json \\
                                      --profiling profiling.json
    python scripts/intake_to_odcs.py --intake intake/intake.example.json \\
                                      --profiling profiling.json --write
"""
from __future__ import annotations
import argparse
import json
import os
import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).parent.parent
SCHEMA_PATH = REPO_ROOT / "schemas" / "intake.schema.json"
DOMAINS_ROOT = REPO_ROOT / "domains"


def _load_json(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _validate_intake(intake: dict) -> None:
    try:
        import jsonschema
    except ImportError:
        sys.stderr.write("[warn] jsonschema nicht installiert — intake-Validierung übersprungen\n")
        return
    schema = _load_json(str(SCHEMA_PATH))
    try:
        jsonschema.validate(intake, schema)
    except jsonschema.ValidationError as e:
        raise ValueError(f"intake.json ungültig: {e.message}") from e


def _parse_frequency(iso: str | None) -> tuple[int, str]:
    """P1D → (1, 'd'),  P1M → (1, 'mo'),  P1W → (1, 'w'),  P1Y → (1, 'y')."""
    if not iso:
        return (1, "d")
    m = re.match(r"^P(\d+)([DWMY])$", iso.upper())
    if not m:
        return (1, "d")
    n, unit = int(m.group(1)), m.group(2)
    return n, {"D": "d", "W": "w", "M": "mo", "Y": "y"}[unit]


def _normalize_name(name: str) -> str:
    """min-temp → min_temp: alles außer Buchstaben/Ziffern/_ zu _ machen."""
    return re.sub(r"[^a-zA-Z0-9_]", "_", name)


def _col_description(raw_name: str, intake_col_map: dict[str, dict]) -> str:
    c = intake_col_map.get(raw_name, {})
    return c.get("description") or f"{raw_name}."


def _profiler_rule_to_odcs(rule: dict, table: str) -> dict | None:
    """Profiler-rule-dict → ODCS-quality-item (engine/customProperties-Konvention)."""
    r = rule.get("rule")
    base: dict = {"type": "text", "dimension": "accuracy", "severity": "error"}
    if r == "not_null":
        col = rule["column"]
        return {**base, "name": f"not_null_{col}",
                "description": f"Spalte {col} ohne Nullwerte.",
                "customProperties": [
                    {"property": "engine", "value": "not_null"},
                    {"property": "column", "value": col},
                ]}
    if r == "unique":
        cols = rule.get("columns") or [rule["column"]]
        col_list = ", ".join(cols)
        name = "unique_" + "_".join(cols)
        label = "Spalte" if len(cols) == 1 else "Spaltenkombination"
        return {**base, "name": name, "dimension": "uniqueness",
                "description": f"{label} {col_list} eindeutig.",
                "customProperties": [
                    {"property": "engine", "value": "sql"},
                    {"property": "query", "value": f"SELECT count(*) FROM (SELECT {col_list} FROM {table} GROUP BY {col_list} HAVING count(*) > 1)"},
                    {"property": "expect", "value": 0},
                ]}
    if r == "range":
        col = rule["column"]
        return {**base, "name": f"range_{col}",
                "description": f"Spalte {col} im Bereich {rule.get('min')}–{rule.get('max')}.",
                "customProperties": [
                    {"property": "engine", "value": "range"},
                    {"property": "column", "value": col},
                    {"property": "min", "value": rule["min"]},
                    {"property": "max", "value": rule["max"]},
                ]}
    if r == "expression":
        expr = rule["expr"]
        safe_name = re.sub(r"[^a-z0-9_]", "_", expr.lower())[:40].strip("_")
        return {**base, "name": safe_name,
                "description": f"Ausdruck: {expr}.",
                "customProperties": [
                    {"property": "engine", "value": "sql"},
                    {"property": "query", "value": f"SELECT count(*) FROM {table} WHERE NOT ({expr})"},
                    {"property": "expect", "value": 0},
                ]}
    return None


def _normalize_rule(rule: dict, col_map: dict[str, str]) -> dict:
    """Normalisiert Spaltennamen in einer quality-rule (für Output-Contract)."""
    r = dict(rule)
    if "column" in r:
        r["column"] = col_map.get(r["column"], r["column"])
    if "columns" in r:
        r["columns"] = [col_map.get(c, c) for c in r["columns"]]
    if "expr" in r:
        expr = r["expr"]
        for old, new in col_map.items():
            if old != new:
                expr = expr.replace(old, new)
        r["expr"] = expr
    return r


def _governance_custom_props(intake: dict) -> list[dict]:
    props: list[dict] = [
        {"property": "classification", "value": intake["classification"]},
        {"property": "contract_status", "value": "active"},
        {"property": "personal_data", "value": intake.get("personal_data", False)},
    ]
    if intake.get("personal_data"):
        props += [
            {"property": "legal_basis", "value": intake.get("legal_basis", "")},
            {"property": "retention_period", "value": intake.get("retention_period", "")},
            {"property": "dpo_notified", "value": True},
        ]
    if intake.get("open_data_candidate"):
        props.append({"property": "open_data_candidate", "value": True})
        props.append({"property": "license", "value": intake.get("license", "")})
        if intake.get("spatial"):
            props.append({"property": "spatial", "value": intake["spatial"]})
        if intake.get("update_frequency"):
            props.append({"property": "accrual_periodicity", "value": intake["update_frequency"]})
        if intake.get("govdata_category"):
            props.append({"property": "govdata_category", "value": intake["govdata_category"]})
    return props


def build_contracts(intake: dict, profiling: dict) -> dict:
    """Baut Input/Output-ODCS-Contracts + data-product.yaml aus intake + profiling."""
    domain = intake["domain"]
    product = intake["product"]
    title = intake["title"]
    desc = intake.get("description", {})
    source = intake["source"]
    freq_val, freq_unit = _parse_frequency(intake.get("update_frequency"))
    custom_props = _governance_custom_props(intake)

    intake_col_map: dict[str, dict] = {c["name"]: c for c in intake.get("columns", [])}
    profiler_cols: list[dict] = profiling.get("columns", [])

    # Profiler-Kandidaten + intake.quality_rules mergen: der Mensch (intake) überschreibt
    # bzw. ergänzt die beobachteten Kandidaten (intake.schema: "überschrieben oder ergänzt").
    def _rule_key(r: dict) -> tuple:
        cols = tuple(r["columns"]) if r.get("columns") else None
        return (r.get("rule"), r.get("column"), cols, r.get("expr"))

    merged: dict[tuple, dict] = {_rule_key(r): r for r in profiling.get("quality_rules", [])}
    for r in intake.get("quality_rules", []):
        merged[_rule_key(r)] = r
    quality_rules: list[dict] = list(merged.values())

    input_table = f"{product}_rohdaten"
    output_table = f"{product}_tageswerte"

    # col_map: raw_name → normalized_name (für Output)
    col_map = {c["name"]: _normalize_name(c["name"]) for c in profiler_cols}

    # --- INPUT: Properties (Rohname beibehalten) ---
    input_props = []
    for c in profiler_cols:
        input_props.append({
            "name": c["name"],
            "logicalType": c["logical_type"],
            "physicalType": c["physical_type"],
            "required": c["null_rate"] == 0.0,
            "description": _col_description(c["name"], intake_col_map),
        })

    # Input-Quality: nur expression + row_count_min
    input_quality = []
    for rule in quality_rules:
        if rule.get("rule") == "expression":
            q = _profiler_rule_to_odcs(rule, input_table)
            if q:
                input_quality.append(q)
    input_quality.append({
        "type": "text", "name": "row_count_min",
        "description": "Mindestens eine Zeile geliefert.",
        "dimension": "completeness", "severity": "error",
        "customProperties": [
            {"property": "engine", "value": "row_count_min"},
            {"property": "min", "value": 1},
        ],
    })

    input_contract = {
        "version": "1.0.0",
        "apiVersion": "v3.1.0",
        "kind": "DataContract",
        "id": f"lhm:{domain}:input:{product}",
        "status": "active",
        "name": f"{title} — Rohdaten",
        "domain": domain,
        "description": {
            "purpose": desc.get("purpose", ""),
            "usage": f"Input-Port des Datenprodukts {product} — Quelle für dlt-Ingestion.",
            "limitations": desc.get("limitations", "Roh, unbereinigt."),
        },
        "servers": [{
            "server": "csv-export",
            "type": "local",
            "description": f"CSV File-Export ({source.get('location', '')}).",
            "path": source.get("location", ""),
            "format": "csv",
        }],
        "schema": [{
            "name": input_table,
            "logicalType": "object",
            "physicalType": "csv",
            "physicalName": os.path.basename(source.get("location", "")),
            "dataGranularityDescription": "Eine Zeile je Datensatz.",
            "properties": input_props,
            "quality": input_quality,
        }],
        "slaProperties": [
            {"property": "frequency", "value": freq_val, "unit": freq_unit},
        ],
        "customProperties": custom_props,
    }

    # --- OUTPUT: Properties (normalisierter Name) ---
    output_props = []
    for c in profiler_cols:
        output_props.append({
            "name": col_map[c["name"]],
            "logicalType": c["logical_type"],
            "physicalType": c["physical_type"],
            "required": c["null_rate"] == 0.0,
            "description": _col_description(c["name"], intake_col_map),
        })

    # Output-Quality: alle Regeln, Spaltennamen normalisiert
    output_quality = []
    for rule in quality_rules:
        norm = _normalize_rule(rule, col_map)
        q = _profiler_rule_to_odcs(norm, output_table)
        if q:
            output_quality.append(q)

    output_contract = {
        "version": "1.0.0",
        "apiVersion": "v3.1.0",
        "kind": "DataContract",
        "id": f"lhm:{domain}:output:{product}",
        "status": "active",
        "name": title,
        "domain": domain,
        "description": {
            "purpose": desc.get("purpose", ""),
            "usage": desc.get("usage", f"Output-Port: dbt-Mart '{output_table}' (View + Parquet-Export)."),
            "limitations": desc.get("limitations", ""),
        },
        "servers": [{
            "server": "hub",
            "type": "duckdb",
            "description": "Demo-Warehouse (warehouse.duckdb); Ziel später Postgres-Hub.",
            "database": "warehouse",
            "schema": "main",
            "customProperties": [
                {"property": "path", "value": "pipeline/dbt/warehouse.duckdb"},
                {"property": "object", "value": output_table},
            ],
        }],
        "schema": [{
            "name": output_table,
            "logicalType": "object",
            "physicalType": "view",
            "physicalName": output_table,
            "dataGranularityDescription": "Eine Zeile je Datensatz.",
            "properties": output_props,
            "quality": output_quality,
        }],
        "slaProperties": [
            {"property": "frequency", "value": freq_val, "unit": freq_unit},
            {"property": "retention", "value": 5, "unit": "y"},
        ],
        "customProperties": custom_props,
    }

    data_product = {
        "id": f"lhm:{domain}:{product}",
        "name": product,
        "title": title,
        "domain": domain,
        "status": "active",
        "source": source,
        "ports": {
            "input": [{
                "id": f"{product}-input",
                "contract": f"contracts/input/{product}.input.odcs.yaml",
                "description": f"Rohdaten {title}.",
            }],
            "output": [{
                "id": f"{product}-output",
                "contract": f"contracts/output/{product}.output.odcs.yaml",
                "description": f"Bereinigte Daten; dbt-Mart '{output_table}'.",
                "serving": [
                    {"type": "db_view", "object": output_table},
                    {"type": "file_export", "format": "parquet"},
                ],
            }],
        },
    }

    return {
        "input_contract": input_contract,
        "output_contract": output_contract,
        "data_product": data_product,
    }


def write_contracts(contracts: dict, domain: str, product: str) -> None:
    product_dir = DOMAINS_ROOT / domain / "data-products" / product
    input_dir = product_dir / "contracts" / "input"
    output_dir = product_dir / "contracts" / "output"
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    paths = {
        "input": input_dir / f"{product}.input.odcs.yaml",
        "output": output_dir / f"{product}.output.odcs.yaml",
        "dp": product_dir / "data-product.yaml",
    }
    for key, data in [("input", contracts["input_contract"]),
                      ("output", contracts["output_contract"]),
                      ("dp", contracts["data_product"])]:
        with open(paths[key], "w", encoding="utf-8") as fh:
            yaml.dump(data, fh, allow_unicode=True, sort_keys=False, default_flow_style=False)
        sys.stderr.write(f"geschrieben: {paths[key]}\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="intake.json + profiling.json → ODCS-Contracts + data-product.yaml")
    ap.add_argument("--intake", required=True, help="Pfad zur intake.json")
    ap.add_argument("--profiling", required=True, help="Pfad zur profiling.json (Profiler-Output)")
    ap.add_argument("--write", action="store_true", help="Dateien schreiben (sonst stdout-Preview)")
    args = ap.parse_args(argv)

    try:
        intake = _load_json(args.intake)
        _validate_intake(intake)
        profiling = _load_json(args.profiling)
    except (FileNotFoundError, ValueError) as e:
        sys.stderr.write(f"Fehler: {e}\n")
        return 1

    contracts = build_contracts(intake, profiling)

    if args.write:
        write_contracts(contracts, intake["domain"], intake["product"])
    else:
        for key, data in [("input_contract", contracts["input_contract"]),
                          ("output_contract", contracts["output_contract"]),
                          ("data_product", contracts["data_product"])]:
            print(f"# --- {key} ---")
            print(yaml.dump(data, allow_unicode=True, sort_keys=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
