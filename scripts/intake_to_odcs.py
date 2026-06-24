#!/usr/bin/env python3
"""intake_to_odcs.py — Workstream B

Schritt 2 der Post-Freigabe-Pipeline. Merged den Profiler-Output (profiling.json,
Spalten/Typen/Quality-Kandidaten) mit den Governance-Feldern aus intake.json
(validiert gegen schemas/intake.schema.json) zu einem finalen ODCS-v3-Contract
+ data-product.yaml unter domains/<domain>/data-products/<product>/.

Aufruf:
    python scripts/intake_to_odcs.py --intake intake/intake.example.json
"""
from __future__ import annotations
import argparse
import json
import sys


def build_contracts(intake: dict) -> dict:
    """intake-dict -> {data_product_yaml, input_contract, output_contract}.

    TODO(Workstream B):
      - templates/contract.template.odcs.yaml + data-product.template.yaml füllen
      - columns -> schema[].properties[] (mit description = LHM-Regel R9)
      - quality_rules -> properties[].quality bzw. objektweit
      - Governance -> customProperties (classification, personal_data, legal_basis,
        retention_period, dpo_notified, open_data_candidate, license, spatial,
        accrual_periodicity, govdata_category)
    """
    raise NotImplementedError("build_contracts: Workstream B")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="intake.json -> ODCS-Contract + data-product.yaml + PR")
    ap.add_argument("--intake", required=True, help="Pfad zur intake.json")
    ap.add_argument("--write", action="store_true", help="Dateien tatsächlich schreiben")
    args = ap.parse_args(argv)

    with open(args.intake, encoding="utf-8") as fh:
        intake = json.load(fh)
    # TODO(Workstream B): gegen schemas/intake.schema.json validieren (jsonschema)
    sys.stderr.write(f"[stub] intake_to_odcs.py: gelesen {args.intake} "
                     f"(domain={intake.get('domain')}, product={intake.get('product')}) — TODO Workstream B\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
