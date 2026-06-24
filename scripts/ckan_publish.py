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
    # CKAN-Freiform-Extras erlauben keine doppelten Schlüssel -> Themes in ein Extra joinen.
    themes = cp.get("govdata_category", [])
    if isinstance(themes, list) and themes:
        extras.append({"key": "theme", "value": ", ".join(themes)})
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
            "url": f"https://github.com/riolties/data-contracts-lhm/tree/main/domains/{contract.get('domain', '')}/",
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


def _ensure_org(base: str, headers: dict, org: str) -> None:
    """Stellt sicher, dass die Ziel-Organisation existiert (best-effort)."""
    if not org:
        return
    import requests
    r = requests.get(f"{base}/api/3/action/organization_show",
                     params={"id": org}, headers=headers, timeout=30)
    if r.ok and r.json().get("success"):
        return
    title = org.replace("-", " ").replace("_", " ").title()
    requests.post(f"{base}/api/3/action/organization_create",
                  data=json.dumps({"name": org, "title": title}),
                  headers=headers, timeout=30)
    sys.stderr.write(f"[org] angelegt: {org}\n")


def _upload_resource(base: str, token: str, pkg_id: str, name: str,
                     fmt: str, description: str, data_file: str) -> None:
    """Lädt eine Datei als CKAN-Ressource hoch (idempotent über den Namen).

    DataPusher der Ziel-CKAN befüllt den Datastore danach automatisch
    (Tabellen-Vorschau). Multipart-Upload -> KEIN JSON-Content-Type.
    """
    import requests
    mp = {"Authorization": token}

    show = requests.get(f"{base}/api/3/action/package_show",
                        params={"id": pkg_id}, headers=mp, timeout=30)
    res_id = None
    if show.ok and show.json().get("success"):
        for res in show.json()["result"].get("resources", []):
            if res.get("name") == name:
                res_id = res["id"]
                break

    data = {"name": name, "format": fmt, "description": description}
    if res_id:
        data["id"] = res_id
        action = "resource_update"
    else:
        data["package_id"] = pkg_id
        action = "resource_create"

    with open(data_file, "rb") as fh:
        resp = requests.post(f"{base}/api/3/action/{action}", data=data,
                             files={"upload": (Path(data_file).name, fh)},
                             headers=mp, timeout=180)
    ok = resp.ok and resp.json().get("success")
    sys.stderr.write(f"[resource] {'ok' if ok else 'err'} {action}: {name}\n")
    if not ok:
        sys.stderr.write(f"  -> {resp.text[:200]}\n")


def publish(contract: dict, ckan_url: str, api_key: str,
            data_file: str | None = None, data_format: str = "CSV") -> int:
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
    # CKAN 2.10+: API-Token im Authorization-Header (X-CKAN-API-Key ist Legacy).
    headers = {"Authorization": api_key, "Content-Type": "application/json"}

    # Ziel-Organisation (= domain) muss existieren; best-effort anlegen.
    _ensure_org(base, headers, pkg.get("owner_org", ""))

    # package_show → entscheidet create vs. update
    link_resources = pkg.pop("resources", [])
    r = requests.get(f"{base}/api/3/action/package_show",
                     params={"id": pkg["name"]}, headers=headers, timeout=30)
    existing_resources: list[dict] = []
    if r.ok and r.json().get("success"):
        existing = r.json()["result"]
        pkg["id"] = existing["id"]
        action = "package_update"
        existing_resources = existing.get("resources", [])
    else:
        action = "package_create"

    # WICHTIG: package_update ERSETZT die Ressourcenliste. Bestehende Ressourcen
    # (inkl. hochgeladener Daten-Ressourcen) daher zurück in den Payload mergen,
    # damit ihre IDs stabil bleiben; Link-Ressourcen per Name aktualisieren.
    by_name = {res.get("name"): res for res in existing_resources}
    for lr in link_resources:
        if lr["name"] in by_name:
            by_name[lr["name"]].update(lr)
        else:
            existing_resources.append(lr)
    pkg["resources"] = existing_resources

    resp = requests.post(f"{base}/api/3/action/{action}",
                         data=json.dumps(pkg), headers=headers, timeout=30)
    resp.raise_for_status()
    result = resp.json()
    if not result.get("success"):
        sys.stderr.write(f"[error] CKAN: {result.get('error')}\n")
        return 1
    sys.stderr.write(f"[ok] {action}: {pkg['name']}\n")

    # Optional: bereinigte Output-Daten als Ressource anhängen (-> Datastore/Vorschau).
    if data_file:
        if not Path(data_file).exists():
            sys.stderr.write(f"[warn] Datendatei nicht gefunden: {data_file}\n")
        else:
            res_name = f"{pkg['title']} ({data_format})"
            res_desc = next((s.get("dataGranularityDescription", "")
                             for s in contract.get("schema", [])), "")
            _upload_resource(base, api_key, result["result"]["id"],
                             res_name, data_format, res_desc, data_file)
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="ODCS-Output-Contract → CKAN publizieren")
    ap.add_argument("--contract", required=True, help="Pfad zum Output-Contract (*.odcs.yaml)")
    ap.add_argument("--ckan-url", default="http://localhost:5000")
    ap.add_argument("--api-key", default=None)
    ap.add_argument("--data-file", default=None,
                    help="Optional: bereinigte Daten (z.B. output/radverkehr_tageswerte.csv) als Ressource anhängen")
    ap.add_argument("--data-format", default="CSV")
    args = ap.parse_args(argv)

    with open(args.contract, encoding="utf-8") as fh:
        contract = yaml.safe_load(fh)

    try:
        return publish(contract, args.ckan_url, args.api_key or "",
                       data_file=args.data_file, data_format=args.data_format)
    except Exception as e:
        sys.stderr.write(f"Fehler: {e}\n")
        return 1


# re wird nur in to_ckan_dataset gebraucht — late import vermeiden
import re  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
