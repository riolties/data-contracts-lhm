#!/usr/bin/env python3
"""ckan_publish.py — Workstream B

Mappt einen ODCS-Output-Contract auf ein CKAN-Dataset (+ DCAT-AP.de-Extras) und
ruft die CKAN-API (package_create/package_update). Nur open_data_candidate=true
und classification=public. Ohne --api-key wird der gemappte Payload angezeigt
(dry-run).

Aufruf:
    python scripts/ckan_publish.py --contract domains/.../contracts/output/....yaml
    python scripts/ckan_publish.py --contract ... --ckan-url http://localhost:5000 --api-key $KEY
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

import yaml

_LICENSE_MAP = {
    "https://www.govdata.de/dl-de/by-2-0": "dl-de-by-2.0",
    "https://www.govdata.de/dl-de/zero-2-0": "dl-de-zero-2.0",
    "https://creativecommons.org/licenses/by/4.0/": "cc-by",
    "https://creativecommons.org/publicdomain/zero/1.0/": "cc-zero",
}


def _cp(contract: dict) -> dict:
    return {c["property"]: c["value"] for c in contract.get("customProperties", [])}


def to_ckan_dataset(contract: dict) -> dict:
    """ODCS-Output-Contract → CKAN-package-Dict inkl. DCAT-AP.de-Extras."""
    cp = _cp(contract)
    contract_id = contract.get("id", "")
    # lhm:domain:output:product → lhm-domain-product
    ckan_name = re.sub(r":output:", "-", contract_id).replace(":", "-")

    desc = contract.get("description", {})
    notes = "\n\n".join(filter(None, [
        desc.get("purpose"), desc.get("usage"), desc.get("limitations")
    ]))

    license_uri = cp.get("license", "")
    license_id = _LICENSE_MAP.get(license_uri, license_uri)

    extras: list[dict] = []
    if cp.get("spatial"):
        extras.append({"key": "spatial_uri", "value": cp["spatial"]})
    if cp.get("accrual_periodicity"):
        extras.append({"key": "frequency", "value": cp["accrual_periodicity"]})
    themes = cp.get("govdata_category", [])
    if isinstance(themes, list):
        for t in themes:
            extras.append({"key": "theme", "value": t})
    elif themes:
        extras.append({"key": "theme", "value": themes})
    extras.append({"key": "contract_id", "value": contract_id})
    extras.append({"key": "classification", "value": cp.get("classification", "")})

    sla_freq = next((s for s in contract.get("slaProperties", [])
                     if s.get("property") == "frequency"), None)
    if sla_freq:
        extras.append({"key": "update_frequency",
                       "value": f"{sla_freq['value']} {sla_freq.get('unit', '')}"})

    resources = []
    for schema_obj in contract.get("schema", []):
        resources.append({
            "name": schema_obj.get("name", ""),
            "format": "view",
            "description": schema_obj.get("dataGranularityDescription", ""),
            "url": f"https://github.com/riolties/data-contracts-lhm/blob/main/domains/{contract.get('domain', '')}/",
        })

    return {
        "name": ckan_name,
        "title": contract.get("name", ""),
        "notes": notes,
        "license_id": license_id,
        "owner_org": contract.get("domain", "lhm"),
        "extras": extras,
        "resources": resources,
    }


def publish(contract: dict, ckan_url: str, api_key: str) -> int:
    cp = _cp(contract)

    if not cp.get("open_data_candidate"):
        sys.stderr.write("[skip] open_data_candidate nicht gesetzt\n")
        return 0
    if cp.get("classification") != "public":
        sys.stderr.write("[skip] classification != public\n")
        return 0

    pkg = to_ckan_dataset(contract)

    if not api_key:
        sys.stderr.write("[dry-run] kein API-Key — Payload wird ausgegeben:\n")
        print(json.dumps(pkg, ensure_ascii=False, indent=2))
        return 0

    try:
        import requests
    except ImportError:
        sys.stderr.write("requests nicht installiert — pip install requests\n")
        return 1

    base = ckan_url.rstrip("/")
    headers = {"X-CKAN-API-Key": api_key, "Content-Type": "application/json"}

    # package_show → entscheidet create vs. update
    r = requests.get(f"{base}/api/3/action/package_show",
                     params={"id": pkg["name"]}, headers=headers, timeout=30)
    if r.ok and r.json().get("success"):
        pkg["id"] = r.json()["result"]["id"]
        action = "package_update"
    else:
        action = "package_create"

    resp = requests.post(f"{base}/api/3/action/{action}",
                         data=json.dumps(pkg), headers=headers, timeout=30)
    resp.raise_for_status()
    result = resp.json()
    if result.get("success"):
        sys.stderr.write(f"[ok] {action}: {pkg['name']}\n")
        return 0
    sys.stderr.write(f"[error] CKAN: {result.get('error')}\n")
    return 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="ODCS-Output-Contract → CKAN publizieren")
    ap.add_argument("--contract", required=True, help="Pfad zum Output-Contract (*.odcs.yaml)")
    ap.add_argument("--ckan-url", default="http://localhost:5000")
    ap.add_argument("--api-key", default=None)
    args = ap.parse_args(argv)

    with open(args.contract, encoding="utf-8") as fh:
        contract = yaml.safe_load(fh)

    try:
        return publish(contract, args.ckan_url, args.api_key or "")
    except Exception as e:
        sys.stderr.write(f"Fehler: {e}\n")
        return 1


# re wird nur in to_ckan_dataset gebraucht — late import vermeiden
import re  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
