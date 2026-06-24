# data-contracts-lhm

Hackathon-Blueprint: **Data Contracts & Data Products als Code** für die Landeshauptstadt München (Data Mesh). Zeigt den kompletten Lebenszyklus eines Datenprodukts — von der Quelle über automatisch abgeleitete **ODCS-v3-Contracts**, **Ingestion (dlt) + Transformation (dbt)**, **Quality Gate** und **Freigabe** bis **CKAN-Katalog** — portierbar auf **GitLab + ServiceNow**.

> Status: Hackathon-Gerüst. Logik in `scripts/` und `pipeline/` ist noch zu implementieren (siehe Issues & `TODO`s).

## Dokumentation
- 📋 [Hackathon-Plan](docs/hackathon-plan.md) — Scope, Architektur, Team-Aufteilung, Timeline
- 🔄 [Intake-, Profiling- & Freigabe-Workflow](docs/workflow-intake-approval.md) — ServiceNow ↔ GitLab
- 🔐 [Output Port & Zugriffskontrolle](docs/access-and-output-port.md)
- 🏛 [Architektur](docs/architecture.md) · [Governance](docs/governance.md) · [Contributing](docs/contributing.md)
- 🤝 [Claude Code Working Agreement](docs/claude-code-working-agreement.md) — Branches, Modellwahl, Stunde-0-Sync

## Repo-Struktur
```
domains/<referat>/data-products/<produkt>/   # Datendomänen = Referate
  data-product.yaml                          # Quelle + Port-Topologie
  contracts/input|output/*.odcs.yaml         # ODCS-v3-Contracts pro Port
schemas/      odcs-v3.schema.json · intake.schema.json · lhm-rules.md
scripts/      profile_source · intake_to_odcs · validate_odcs · run_quality · ckan_publish · render_catalog · apply_access
pipeline/     ingest/ (dlt) · dbt/ (dbt-duckdb)
intake/       servicenow-catalog-item.md · intake.example.json
ckan/         docker-compose.yml (lokale CKAN)
data/         CSV-Sample (Demo-Quelle)
.github/      ISSUE_TEMPLATE/ · workflows/
```

## Quickstart (lokal)
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Schema aus den Daten ableiten (Workstream A)
python scripts/profile_source.py --source data/sample_radverkehr_tageswerte_2025_01.csv

# Contract gegen ODCS + LHM-Regeln validieren (Workstream B/C)
python scripts/validate_odcs.py "domains/**/contracts/**/*.odcs.yaml"

# Pipeline + Quality (Workstream C)
python pipeline/ingest/load_csv.py
cd pipeline/dbt && dbt build   # dbt-duckdb
```

## Beispiel-Datenprodukt
**Mobilitätsreferat / `radverkehr`** auf Basis der offenen [Raddauerzählstellen München](https://opendata.muenchen.de/dataset/daten-der-raddaten-muenchen-2025) (Lizenz dl-by-de/2.0). Sample unter `data/`.

## Workstreams
- **A** — Domänen, Contracts & Profiler · **B** — Intake, Freigabe, Validierung & Katalog · **C** — Data Pipeline & Quality + Output Port. Siehe [Issues](../../issues).
