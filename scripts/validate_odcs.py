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
import sys


def lhm_rule_errors(contract: dict, is_output: bool) -> list[str]:
    """LHM-Regeln R1–R10 (siehe schemas/lhm-rules.md). TODO(Workstream B/C).

    Tipp: cp = {c["property"]: c["value"] for c in contract.get("customProperties", [])}
    """
    raise NotImplementedError("lhm_rule_errors: Workstream B/C")


def validate_file(path: str, schema: dict) -> list[str]:
    """Ein Contract: jsonschema + LHM-Regeln. Liefert Fehlerliste (leer = ok)."""
    raise NotImplementedError("validate_file: Workstream B/C")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="ODCS + LHM-Regeln validieren")
    ap.add_argument("patterns", nargs="*", default=["domains/**/contracts/**/*.odcs.yaml"],
                    help="Glob-Pattern für *.odcs.yaml")
    args = ap.parse_args(argv)

    files = sorted({f for p in args.patterns for f in glob.glob(p, recursive=True)})
    if not files:
        sys.stderr.write("[stub] keine *.odcs.yaml gefunden — noch keine Contracts (Workstream A)\n")
        return 0
    # TODO(Workstream B/C): schemas/odcs-v3.schema.json laden, je Datei validieren,
    #   Fehler sammeln, bei Fehlern Exit 1.
    sys.stderr.write(f"[stub] validate_odcs.py: {len(files)} Datei(en) gefunden — Validierung TODO\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
