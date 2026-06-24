#!/usr/bin/env python3
"""seed_demo.py — CKAN-Demo-Portal befüllen (Workstream C / CKAN-Integration)

Legt die Fachreferate als CKAN-Organisationen an und erzeugt eine Handvoll
plausibler Demo-Datensätze, damit das Portal (ckan.davb.dev) wie ein echtes
Open-Data-Portal der Landeshauptstadt München aussieht (vgl. opendata.muenchen.de).

Der *echte* Datensatz `radverkehr` kommt aus der Pipeline über
`scripts/ckan_publish.py` (aus dem Output-Contract) — dieses Skript ergänzt
nur den Demo-Kontext drumherum. Idempotent: bestehende Datensätze/Orgs werden
aktualisiert statt doppelt angelegt.

Aufruf:
    export CKAN_API_KEY=<token>
    python ckan/seed_demo.py --ckan-url https://ckan.davb.dev
"""
from __future__ import annotations
import argparse
import json
import os
import sys

import requests

DL_DE_BY = "dl-de-by-2.0"
TRAN = "http://publications.europa.eu/resource/authority/data-theme/TRAN"
ENVI = "http://publications.europa.eu/resource/authority/data-theme/ENVI"
GOVE = "http://publications.europa.eu/resource/authority/data-theme/GOVE"
SOCI = "http://publications.europa.eu/resource/authority/data-theme/SOCI"
REGI = "http://publications.europa.eu/resource/authority/data-theme/REGI"
TECH = "http://publications.europa.eu/resource/authority/data-theme/TECH"
MUC = "https://sws.geonames.org/2867714/"  # München

ORGS = [
    ("mobilitaetsreferat", "Mobilitätsreferat",
     "Datenprodukte des Mobilitätsreferats der Landeshauptstadt München (z. B. Radverkehr)."),
    ("kreisverwaltungsreferat", "Kreisverwaltungsreferat (KVR)",
     "Datenprodukte des Kreisverwaltungsreferats der Landeshauptstadt München."),
    ("referat-fuer-stadtplanung-und-bauordnung", "Referat für Stadtplanung und Bauordnung",
     "Datenprodukte des Referats für Stadtplanung und Bauordnung."),
    ("referat-fuer-klima-und-umweltschutz", "Referat für Klima- und Umweltschutz",
     "Datenprodukte des Referats für Klima- und Umweltschutz."),
    ("it-referat", "IT-Referat",
     "Datenprodukte und Basisdienste des IT-Referats der Landeshauptstadt München."),
]

# Demo-Datensätze (Metadaten). Bewusst als Demo gekennzeichnet.
DATASETS = [
    {
        "name": "mvg-mietraeder-stationen",
        "title": "MVG Rad – Stationen",
        "owner_org": "mobilitaetsreferat",
        "notes": "Standorte der MVG-Rad-Stationen im Stadtgebiet München. "
                 "**Demo-Datensatz** des Data-Mesh-Hackathons.",
        "themes": [TRAN], "freq": "P1M",
    },
    {
        "name": "luftqualitaet-messstationen",
        "title": "Luftqualität – Messstationen",
        "owner_org": "referat-fuer-klima-und-umweltschutz",
        "notes": "Tagesmittelwerte der Luftschadstoffe (NO₂, PM10) je Messstation. "
                 "**Demo-Datensatz** des Data-Mesh-Hackathons.",
        "themes": [ENVI], "freq": "P1D",
    },
    {
        "name": "baumkataster",
        "title": "Baumkataster München",
        "owner_org": "referat-fuer-klima-und-umweltschutz",
        "notes": "Standorte und Arten der städtischen Bäume. "
                 "**Demo-Datensatz** des Data-Mesh-Hackathons.",
        "themes": [ENVI, REGI], "freq": "P1Y",
    },
    {
        "name": "bevoelkerungsbestand-stadtbezirke",
        "title": "Bevölkerungsbestand nach Stadtbezirken",
        "owner_org": "kreisverwaltungsreferat",
        "notes": "Einwohnerzahlen je Stadtbezirk und Jahr. "
                 "**Demo-Datensatz** des Data-Mesh-Hackathons.",
        "themes": [SOCI, GOVE], "freq": "P1Y",
    },
    {
        "name": "bebauungsplaene",
        "title": "Bebauungspläne München",
        "owner_org": "referat-fuer-stadtplanung-und-bauordnung",
        "notes": "Rechtsverbindliche Bebauungspläne als Geodaten. "
                 "**Demo-Datensatz** des Data-Mesh-Hackathons.",
        "themes": [REGI, GOVE], "freq": "P1M",
    },
    {
        "name": "m-wlan-hotspots",
        "title": "M-WLAN Hotspots",
        "owner_org": "it-referat",
        "notes": "Standorte der öffentlichen WLAN-Hotspots (M-WLAN). "
                 "**Demo-Datensatz** des Data-Mesh-Hackathons.",
        "themes": [TECH], "freq": "P1M",
    },
]


def api(base: str, action: str, headers: dict, payload: dict | None = None,
        method: str = "post"):
    url = f"{base}/api/3/action/{action}"
    if method == "get":
        return requests.get(url, params=payload, headers=headers, timeout=30)
    return requests.post(url, data=json.dumps(payload or {}), headers=headers, timeout=30)


def ensure_org(base: str, headers: dict, name: str, title: str, desc: str) -> None:
    r = api(base, "organization_show", headers, {"id": name}, "get")
    if r.ok and r.json().get("success"):
        return
    r = api(base, "organization_create", headers,
            {"name": name, "title": title, "description": desc})
    print(f"[org] {'ok' if r.ok and r.json().get('success') else 'err'}: {name}")


def upsert_dataset(base: str, headers: dict, ds: dict) -> None:
    extras = [{"key": "frequency", "value": ds["freq"]},
              {"key": "spatial_uri", "value": MUC},
              {"key": "demo", "value": "true"}]
    # CKAN-Freiform-Extras erlauben keine doppelten Schlüssel -> Themes joinen.
    if ds["themes"]:
        extras.append({"key": "theme", "value": ", ".join(ds["themes"])})
    pkg = {
        "name": ds["name"], "title": ds["title"], "notes": ds["notes"],
        "owner_org": ds["owner_org"], "license_id": DL_DE_BY,
        "private": False, "extras": extras,
    }
    show = api(base, "package_show", headers, {"id": ds["name"]}, "get")
    if show.ok and show.json().get("success"):
        pkg["id"] = show.json()["result"]["id"]
        action = "package_update"
    else:
        action = "package_create"
    r = api(base, action, headers, pkg)
    ok = r.ok and r.json().get("success")
    print(f"[ds] {'ok' if ok else 'err'} {action}: {ds['name']}"
          + ("" if ok else f" -> {r.text[:200]}"))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="CKAN-Demo-Portal befüllen")
    ap.add_argument("--ckan-url", default="https://ckan.davb.dev")
    ap.add_argument("--api-key", default=os.environ.get("CKAN_API_KEY"))
    args = ap.parse_args(argv)

    if not args.api_key:
        sys.stderr.write("Kein API-Key (--api-key oder CKAN_API_KEY).\n")
        return 1

    base = args.ckan_url.rstrip("/")
    headers = {"Authorization": args.api_key, "Content-Type": "application/json"}

    for name, title, desc in ORGS:
        ensure_org(base, headers, name, title, desc)
    for ds in DATASETS:
        upsert_dataset(base, headers, ds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
