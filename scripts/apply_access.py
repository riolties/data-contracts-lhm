#!/usr/bin/env python3
"""apply_access.py — Workstream C (Stretch)

Leitet aus roles[]/classification eines Output-Contracts die Zugriffspolicy ab:
- PostgreSQL GRANT-Statements (read_dp_<produkt> -> SELECT auf die View)
- access-policy.json (Keycloak-Group -> Rolle -> Objekt)
Im Hackathon wird das ARTEFAKT erzeugt/gezeigt (kein Live-Keycloak/Postgres).
Siehe docs/access-and-output-port.md.

Aufruf:
    python scripts/apply_access.py --contract <output.odcs.yaml> --out-sql grants.sql --out-policy access-policy.json
"""
from __future__ import annotations
import argparse
import sys


def derive_access(contract: dict) -> tuple[str, dict]:
    """Contract -> (grants_sql, access_policy_dict). TODO(Workstream C)."""
    raise NotImplementedError("derive_access: Workstream C")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Contract -> GRANTs + access-policy.json")
    ap.add_argument("--contract", required=True)
    ap.add_argument("--out-sql", default="grants.sql")
    ap.add_argument("--out-policy", default="access-policy.json")
    args = ap.parse_args(argv)
    sys.stderr.write(f"[stub] apply_access.py: {args.contract} — TODO Workstream C\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
