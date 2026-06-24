#!/usr/bin/env python3
"""ckan_publish.py — Workstream B

Mappt einen ODCS-Output-Contract auf ein CKAN-Dataset (+ DCAT-AP.de-Extras) und
ruft die CKAN-API (package_create/package_update). Nur open_data_candidate=true.

Aufruf:
    python scripts/ckan_publish.py --contract <output.odcs.yaml> --ckan-url http://localhost:5000 --api-key $CKAN_KEY
"""
from __future__ import annotations
import argparse
import sys

# Mapping ODCS/LHM -> CKAN (siehe docs/access-and-output-port.md & hackathon-plan.md)
#   info/name->title, description->notes, owner->owner_org, tags->tags,
#   license->license_id, spatial->extras.spatial_uri, accrual_periodicity->extras.frequency,
#   govdata_category->extras.theme, classification/contract_status->extras.*


def to_ckan_dataset(contract: dict) -> dict:
    """ODCS-Contract -> CKAN package-dict. TODO(Workstream B)."""
    raise NotImplementedError("to_ckan_dataset: Workstream B")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="ODCS -> CKAN publizieren")
    ap.add_argument("--contract", required=True)
    ap.add_argument("--ckan-url", default="http://localhost:5000")
    ap.add_argument("--api-key", default=None)
    args = ap.parse_args(argv)
    sys.stderr.write(f"[stub] ckan_publish.py: {args.contract} -> {args.ckan_url} — TODO Workstream B\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
