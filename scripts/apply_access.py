#!/usr/bin/env python3
"""apply_access.py — Workstream C (Stretch)

Leitet aus roles[]/classification eines Output-Contracts die Zugriffspolicy ab:
- PostgreSQL GRANT-Statements (read_dp_<produkt> -> SELECT auf die View)
- access-policy.json (Keycloak-Group -> Rolle -> Objekt)
Im Hackathon wird das ARTEFAKT erzeugt/gezeigt (kein Live-Keycloak/Postgres).
Siehe docs/access-and-output-port.md.

Der Contract ist die Control Plane: classification + roles[] deklarieren, wer
lesen darf. Für classification=public (Open Data) gibt es keinen RBAC-Zwang —
es wird ein GRANT ... TO PUBLIC erzeugt und im Policy-JSON als public markiert.

Aufruf:
    python scripts/apply_access.py --contract <output.odcs.yaml> \\
        --out-sql grants.sql --out-policy access-policy.json
"""
from __future__ import annotations
import argparse
import json
import sys

import yaml


def _props(obj: dict) -> dict:
    """customProperties-Liste -> dict {property: value}."""
    return {cp["property"]: cp["value"] for cp in obj.get("customProperties", [])}


def _output_object(contract: dict) -> tuple[str, str]:
    """(schema, object) des Output Ports aus servers[]/schema[] ableiten."""
    schema = "public"
    obj = None
    servers = contract.get("servers") or []
    if servers:
        srv = servers[0]
        schema = srv.get("schema") or schema
        obj = _props(srv).get("object")
    if not obj:
        sch = contract.get("schema") or []
        if sch:
            obj = sch[0].get("physicalName") or sch[0].get("name")
    return schema, (obj or "unknown_object")


def derive_access(contract: dict) -> tuple[str, dict]:
    """Contract -> (grants_sql, access_policy_dict)."""
    cp = _props(contract)
    classification = cp.get("classification")
    personal_data = cp.get("personal_data")
    open_data = cp.get("open_data_candidate")
    schema, obj = _output_object(contract)
    fq = f"{schema}.{obj}"
    is_public = str(classification).lower() == "public"

    policy = {
        "data_product": contract.get("id"),
        "object": fq,
        "classification": classification,
        "personal_data": personal_data,
        "open_data_candidate": open_data,
        "public_access": is_public,
        "roles": [],
    }

    lines = [
        "-- Generiert von apply_access.py aus dem Output-Contract (NICHT von Hand editieren).",
        f"-- Datenprodukt: {contract.get('id')}",
        f"-- Objekt (Output Port): {fq}",
        f"-- Klassifizierung: {classification} | personenbezogen: {personal_data}",
        "",
    ]

    if is_public:
        lines += [
            "-- classification=public -> Open-Data-Lesezugriff für alle.",
            f"GRANT USAGE ON SCHEMA {schema} TO PUBLIC;",
            f"GRANT SELECT ON {fq} TO PUBLIC;",
            "",
        ]

    roles = contract.get("roles") or []
    for role in roles:
        rolename = role.get("role")
        access = role.get("access", "read")
        kc_group = _props(role).get("keycloak_group")
        priv = "SELECT" if access in ("read", "ro", "select") else "SELECT"
        lines += [
            f"-- Rolle: {rolename} (access={access}) <- Keycloak-Gruppe: {kc_group}",
            f"DO $$ BEGIN CREATE ROLE {rolename}; EXCEPTION WHEN duplicate_object THEN NULL; END $$;",
            f"GRANT USAGE ON SCHEMA {schema} TO {rolename};",
            f"GRANT {priv} ON {fq} TO {rolename};",
            "",
        ]
        policy["roles"].append(
            {
                "role": rolename,
                "access": access,
                "keycloak_group": kc_group,
                "object": fq,
            }
        )

    if not is_public and not roles:
        lines += [
            "-- WARNUNG: weder classification=public noch roles[] deklariert —",
            "-- kein Zugriff generiert. Output-Contract sollte roles[] definieren.",
            "",
        ]

    return "\n".join(lines), policy


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Contract -> GRANTs + access-policy.json")
    ap.add_argument("--contract", required=True)
    ap.add_argument("--out-sql", default="grants.sql")
    ap.add_argument("--out-policy", default="access-policy.json")
    args = ap.parse_args(argv)

    with open(args.contract, encoding="utf-8") as fh:
        contract = yaml.safe_load(fh)

    grants_sql, policy = derive_access(contract)

    with open(args.out_sql, "w", encoding="utf-8") as fh:
        fh.write(grants_sql)
    with open(args.out_policy, "w", encoding="utf-8") as fh:
        json.dump(policy, fh, indent=2, ensure_ascii=False)

    sys.stderr.write(
        f"[apply_access] {args.contract} -> {args.out_sql} ({len(policy['roles'])} Rolle(n)), "
        f"{args.out_policy}\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
