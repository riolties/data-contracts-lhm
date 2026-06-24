#!/usr/bin/env python3
"""render_catalog.py — Workstream B

Rendert je Datenprodukt eine Markdown-Katalogseite (README.md im Produktordner)
aus data-product.yaml + den ODCS-Contracts: Titel, Owner, Ports, Schema-Tabelle,
Klassifizierung, SLA, Quality-Regeln, Open-Data-Status.

Aufruf:
    python scripts/render_catalog.py --product domains/mobilitaetsreferat/data-products/radverkehr
    python scripts/render_catalog.py --product domains/mobilitaetsreferat/data-products/radverkehr --write
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

import yaml


def _cp(contract: dict) -> dict:
    return {c["property"]: c["value"] for c in contract.get("customProperties", [])}


def _load(path: Path) -> dict:
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _badge_url(label: str, value: str, color: str) -> str:
    v = value.replace("-", "--").replace(" ", "_")
    l = label.replace(" ", "_")
    return f"![{label}](https://img.shields.io/badge/{l}-{v}-{color})"


_CLS_COLOR = {"public": "brightgreen", "internal": "yellow", "confidential": "red"}


def render(product_dir: str) -> str:
    pdir = Path(product_dir)
    dp = _load(pdir / "data-product.yaml")

    def _load_contract(rel: str) -> dict | None:
        p = pdir / rel
        return _load(p) if p.exists() else None

    input_contracts = [c for port in dp.get("ports", {}).get("input", [])
                       if (c := _load_contract(port["contract"])) is not None]
    output_contracts = [c for port in dp.get("ports", {}).get("output", [])
                        if (c := _load_contract(port["contract"])) is not None]

    title = dp.get("title", dp.get("name", ""))
    domain = dp.get("domain", "")
    cp_out = _cp(output_contracts[0]) if output_contracts else {}
    classification = cp_out.get("classification", "unbekannt")
    personal_data = cp_out.get("personal_data") is True
    open_data = cp_out.get("open_data_candidate") is True
    license_val = cp_out.get("license", "")

    badge = _badge_url("Klassifizierung", classification,
                       _CLS_COLOR.get(classification, "lightgrey"))
    od_badge = _badge_url("Open_Data", "ja", "brightgreen") if open_data else ""

    L: list[str] = [
        f"# {title}",
        "",
        f"> Datenprodukt der Domäne **{domain}** · {badge} {od_badge}".rstrip(),
        "",
    ]

    # Beschreibung
    if output_contracts:
        d = output_contracts[0].get("description", {})
        if d.get("purpose"):
            L += [f"**Zweck:** {d['purpose']}", ""]
        if d.get("usage"):
            L += [f"**Nutzung:** {d['usage']}", ""]
        if d.get("limitations"):
            L += [f"**Einschränkungen:** {d['limitations']}", ""]

    # Metadaten-Tabelle
    source = dp.get("source", {})
    L += ["## Metadaten", "", "| | |", "|---|---|"]
    rows = [
        ("Domäne", domain),
        ("Produkt-ID", dp.get("id", "")),
        ("Status", dp.get("status", "")),
        ("Quelle", f"`{source.get('type', '')}` · `{source.get('location', '')}`"),
        ("Klassifizierung", f"`{classification}`"),
        ("Personenbezogen", "✅ Ja" if personal_data else "Nein"),
    ]
    if open_data:
        rows.append(("Open Data", f"✅ Ja · [Lizenz]({license_val})" if license_val else "✅ Ja"))
    else:
        rows.append(("Open Data", "Nein"))
    if cp_out.get("govdata_category"):
        cats = cp_out["govdata_category"]
        rows.append(("GovData-Kategorie", ", ".join(cats) if isinstance(cats, list) else cats))
    if output_contracts:
        for s in output_contracts[0].get("slaProperties", []):
            rows.append((f"SLA {s['property']}", f"{s['value']} {s.get('unit', '')}"))
    for k, v in rows:
        L.append(f"| **{k}** | {v} |")
    L.append("")

    # Ports
    L += ["## Ports", ""]
    for port in dp.get("ports", {}).get("input", []):
        L.append(f"- **Input** `{port['id']}` — {port.get('description', '')} → [`{port['contract']}`]({port['contract']})")
    for port in dp.get("ports", {}).get("output", []):
        serving = ", ".join(s.get("type", "") for s in port.get("serving", []))
        L.append(f"- **Output** `{port['id']}` — {port.get('description', '')} → [`{port['contract']}`]({port['contract']}) ({serving})")
    L.append("")

    # Schema-Tabelle (Output)
    for contract in output_contracts:
        for schema_obj in contract.get("schema", []):
            L += [
                f"## Schema — `{schema_obj['name']}`",
                "",
                f"*{schema_obj.get('dataGranularityDescription', '')}*",
                "",
                "| Spalte | Typ | Pflicht | Beschreibung |",
                "|---|---|:---:|---|",
            ]
            for prop in schema_obj.get("properties", []):
                req = "✓" if prop.get("required") else ""
                L.append(f"| `{prop['name']}` | `{prop.get('logicalType', '')}` | {req} | {prop.get('description', '')} |")
            L.append("")

            quality = schema_obj.get("quality", [])
            if quality:
                L += ["### Quality-Regeln", "", "| Name | Engine | Beschreibung | Severity |", "|---|---|---|:---:|"]
                for q in quality:
                    qcp = {c["property"]: c["value"] for c in q.get("customProperties", [])}
                    engine = qcp.get("engine", q.get("type", ""))
                    sev = q.get("severity", "")
                    L.append(f"| `{q.get('name', '')}` | `{engine}` | {q.get('description', '')} | {sev} |")
                L.append("")

    # Input-Schema (kompakt)
    for contract in input_contracts:
        cp_in = _cp(contract)
        L += [
            "## Input-Port (Rohdaten)",
            "",
            f"Quelle: `{cp_in.get('classification', '')}` · Server: CSV File-Export",
            "",
        ]
        for schema_obj in contract.get("schema", []):
            L += [
                f"| Spalte | Typ | Pflicht |",
                "|---|---|:---:|",
            ]
            for prop in schema_obj.get("properties", []):
                req = "✓" if prop.get("required") else ""
                L.append(f"| `{prop['name']}` | `{prop.get('logicalType', '')}` | {req} |")
            L.append("")

    L += [
        "---",
        "",
        "*Generiert von `scripts/render_catalog.py` aus `data-product.yaml` + ODCS-Contracts.*",
    ]
    return "\n".join(L) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Datenprodukt → Markdown-Katalogseite")
    ap.add_argument("--product", required=True, help="Pfad zum Produktordner")
    ap.add_argument("--write", action="store_true", help="README.md schreiben")
    args = ap.parse_args(argv)

    try:
        md = render(args.product)
    except FileNotFoundError as e:
        sys.stderr.write(f"Fehler: {e}\n")
        return 1

    if args.write:
        readme = Path(args.product) / "README.md"
        readme.write_text(md, encoding="utf-8")
        sys.stderr.write(f"geschrieben: {readme}\n")
    else:
        print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
