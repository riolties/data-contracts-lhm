#!/usr/bin/env python3
"""validate_odcs.py — Workstream B/C

Validiert ODCS-Contracts (1) gegen schemas/odcs-v3.schema.json (jsonschema) und
(2) gegen die LHM-Regeln aus schemas/lhm-rules.md. Exit != 0 bei Fehler.

Aufruf:
    python scripts/validate_odcs.py "domains/**/contracts/**/*.odcs.yaml"
"""
from __future__ import annotations
import argparse
import glob
import json
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).parent.parent
ODCS_SCHEMA_PATH = REPO_ROOT / "schemas" / "odcs-v3.schema.json"


def _cp(contract: dict) -> dict:
    """customProperties als {property: value}-Dict."""
    return {c["property"]: c["value"] for c in contract.get("customProperties", [])}


# --- LHM-Regeln R1–R10 (je eine Funktion → leicht testbar) ---

def _r1_r2(cp: dict) -> list[str]:
    errors = []
    if "classification" not in cp:
        errors.append("R1: classification fehlt (public|internal|confidential)")
    elif cp["classification"] not in ("public", "internal", "confidential"):
        errors.append(f"R2: classification ungültig: '{cp['classification']}'")
    return errors


def _r3(cp: dict) -> list[str]:
    return [] if "contract_status" in cp else ["R3: contract_status fehlt"]


def _r4(cp: dict) -> list[str]:
    return [] if "personal_data" in cp else ["R4: personal_data fehlt"]


def _r5(cp: dict) -> list[str]:
    if cp.get("personal_data") is not True:
        return []
    errors = []
    if not cp.get("legal_basis"):
        errors.append("R5: personal_data=true aber legal_basis fehlt")
    if not cp.get("retention_period"):
        errors.append("R5: personal_data=true aber retention_period fehlt")
    return errors


def _r6(cp: dict) -> list[str]:
    if cp.get("personal_data") is not True:
        return []
    return [] if cp.get("dpo_notified") is True else ["R6: personal_data=true aber dpo_notified fehlt/nicht true"]


def _r7(cp: dict) -> list[str]:
    if cp.get("open_data_candidate") is not True:
        return []
    errors = []
    for field in ("license", "spatial", "govdata_category"):
        if not cp.get(field):
            errors.append(f"R7: open_data_candidate=true aber {field} fehlt")
    return errors


def _r8(cp: dict) -> list[str]:
    if cp.get("open_data_candidate") is not True:
        return []
    return [] if cp.get("classification") == "public" else [
        "R8: open_data_candidate=true aber classification ist nicht 'public'"
    ]


def _r9(contract: dict) -> list[str]:
    errors = []
    for schema_obj in contract.get("schema", []):
        for prop in schema_obj.get("properties", []):
            if not prop.get("description"):
                errors.append(f"R9: Spalte '{prop.get('name')}' ohne Beschreibung")
    return errors


def _r10(contract: dict) -> list[str]:
    total = sum(len(s.get("quality", [])) for s in contract.get("schema", []))
    return [] if total > 0 else ["R10: Output-Port ohne Quality-Regeln"]


def lhm_rule_errors(contract: dict, is_output: bool) -> list[str]:
    cp = _cp(contract)
    errors = (
        _r1_r2(cp) + _r3(cp) + _r4(cp)
        + _r5(cp) + _r6(cp) + _r7(cp) + _r8(cp)
        + _r9(contract)
        + (_r10(contract) if is_output else [])
    )
    return errors


def validate_file(path: str, odcs_schema: dict) -> list[str]:
    errors: list[str] = []

    try:
        with open(path, encoding="utf-8") as fh:
            contract = yaml.safe_load(fh)
    except Exception as e:
        return [f"YAML-Fehler: {e}"]

    if not contract:
        return ["Leere Datei"]

    # (1) ODCS JSON-Schema-Validierung
    try:
        import jsonschema
        try:
            jsonschema.validate(contract, odcs_schema)
        except jsonschema.ValidationError as e:
            loc = "/".join(str(p) for p in e.absolute_path) or "(root)"
            errors.append(f"ODCS-Schema [{loc}]: {e.message}")
    except ImportError:
        sys.stderr.write("[warn] jsonschema nicht installiert — ODCS-Schema-Check übersprungen\n")

    # (2) LHM-Regeln
    is_output = ".output." in path or ":output:" in (contract.get("id") or "")
    errors.extend(lhm_rule_errors(contract, is_output))

    return errors


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="ODCS + LHM-Regeln validieren")
    ap.add_argument("patterns", nargs="*", default=["domains/**/contracts/**/*.odcs.yaml"],
                    help="Glob-Pattern für *.odcs.yaml")
    args = ap.parse_args(argv)

    files = sorted({f for p in args.patterns for f in glob.glob(p, recursive=True)})
    if not files:
        sys.stderr.write("[info] keine *.odcs.yaml gefunden — nichts zu validieren\n")
        return 0

    with open(ODCS_SCHEMA_PATH, encoding="utf-8") as fh:
        odcs_schema = json.load(fh)

    results: dict[str, list[str]] = {path: validate_file(path, odcs_schema) for path in files}

    for path, errs in results.items():
        status = "✅" if not errs else "❌"
        print(f"{status} {path}")
        for e in errs:
            print(f"   {e}")

    n_errors = sum(len(e) for e in results.values())
    n_failed = sum(1 for e in results.values() if e)

    if n_errors:
        print(f"\n{n_errors} Fehler in {n_failed}/{len(files)} Datei(en) — Gate rot")
        return 1
    print(f"\n{len(files)} Datei(en) valide — Gate grün")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
