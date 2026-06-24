# Hackathon-Plan: Data Contracts & Data Products mit Pipeline (LHM)

## Context

Die Landeshauptstadt München (DAICE + aufzubauendes Data Office) baut ein **Data Mesh**, in dem **Data Contracts die Governance-Grundlage** bilden. Datendomänen sind organisatorisch die **Referate**. Phase-1-Pilot: **EWO** (Produzent, Adressdaten) → **Mobilitätsreferat** (Konsument). Vorhandener LHM-Werkzeugkasten: R, SPSS, Python, **GitLab Runners**, **dbt**, Node-RED, VS Code, **FME**; Daten liegen in Fachverfahren/DBs (Postgres, Oracle), angebunden über Reporting-DB, manuellen File-Export, Laufwerke oder EAI-Schnittstelle. Ziel-Stack: PostgreSQL, dbt, dlt, Keycloak, CKAN + `ckanext-dcat` → GovData. Rollen: **Datenverantwortliche/Dateneigner (Data Owner)**, **Data Steward**, **Datenschutzbeauftragte (DSB)**.

Ziel des Hackathons (3 Personen, 12 h): In einem **GitHub-Repo** (`riolties/data-contracts-lhm`) den **kompletten Lebenszyklus eines Datenprodukts als Code** zeigen — von der **Datenquelle** über **automatisch abgeleitete Contracts**, **Ingestion (dlt) + Transformation (dbt)**, **Quality Gate** und **Freigabe** bis **CKAN-Katalog** — 1:1 portierbar auf **GitLab + ServiceNow**.

**Bestätigte Festlegungen:**
- Standard: **ODCS (Bitol) v3.1.0** (vendored JSON-Schema).
- Ausrichtung: **Full Pipeline inkl. dbt** (nicht nur Metadaten).
- **Contract aus den Daten ziehen:** ein **Profiler** leitet technisches Schema + Kandidaten-Quality-Regeln aus der Quelle ab; der Mensch ergänzt via ServiceNow nur Governance-Felder.
- Quell-Connector in der Demo: **nur CSV File-Export** (repräsentiert „manueller File-Export aus Fachverfahren"). Quelle wird über `source.type` abstrahiert (`file_export | reporting_db | network_drive | eai`), weitere Connectoren später.
- Lokales Warehouse: **DuckDB** (dlt-Load + **dbt-duckdb**) — kein DB-Server nötig, GitLab-Runner-tauglich.
- **Intake/Governance: ServiceNow-Katalogformular**; ServiceNow **triggert** die Pipeline (REST/Trigger-Token), **GitLab-CI öffnet den Merge Request** (lose Kopplung). Im Hackathon via `repository_dispatch`/Issue-Form abgebildet.
- **Freigabe: ServiceNow** mehrstufig (Dateneigner; + DSB wenn `personal_data: true`). Im Hackathon über PR-Labels (`owner-approved`, `dsb-approved`) simuliert.
- **Quality Gate** (bleibt, weil Pipeline): Contract-Regeln + **dbt-Tests** laufen gegen die **materialisierten Daten**, nicht gegen ein statisches Sample.
- **CKAN-Demo: lokale CKAN via Docker.**
- Beispiel: **Mobilitätsreferat / „radverkehr"** auf Basis der **Raddauerzählstellen** (opendata.muenchen.de, Lizenz dl-by-de/2.0).

**Vertiefende Designs:**
- [Intake-, Profiling- & Freigabe-Workflow (ServiceNow ↔ GitLab)](workflow-intake-approval.md) — 6-Phasen-Sequenz, bidirektionale Kopplung, dynamisches Formular, Validierung-vor-Freigabe.
- [Output Port & Zugriffskontrolle](access-and-output-port.md) — Bereitstellung (View/Datei/API/Open-Data) + contract-getriebenes RBAC (Keycloak + Postgres-Grants).

---

## Lebenszyklus (Zielbild)

```
Quelle: CSV File-Export aus Fachverfahren (Raddaten)
   │  profile_source.py  →  Schema + Kandidaten-Quality-Regeln (technisch)
   ▼
Draft-ODCS (technisch)            ServiceNow-Katalogformular (Governance:
   │                              Owner, Klassifizierung, Rechtsgrundlage,
   │                              DSGVO-Flag, Open-Data, Beschreibungen)
   └───────────────┬───────────────────────┘
                   │ intake_to_odcs.py  (merge technisch + Governance)
                   │ ServiceNow ──trigger(intake.json)──►  GitLab-CI öffnet MR
                   ▼
         PR/MR: data-product.yaml + *.odcs.yaml
                   │
     ┌─────────────┼───────────────┬───────────────────────────┐
     ▼             ▼               ▼                           ▼
 validate-      approval-gate   PIPELINE-BUILD:            (auf PR)
 contracts     (Owner + DSB)    dlt: CSV → DuckDB(raw)
 (ODCS+LHM)                     dbt: raw → radverkehr_tageswerte
                                quality-gate: Contract-Regeln + dbt-Tests
                                              vs. materialisierte Daten
     └─────────────┴───────────────┴───────────────────────────┘
                   ▼ alle grün + Freigaben → Merge
        publish-ckan-catalog → CKAN (lokal/Docker) + DCAT-AP.de-Extras
                              + gerenderte Katalogseite
```

Kein Mensch tippt technisches Schema; kein LLM im kritischen Pfad.

---

## ServiceNow ↔ GitLab (Ziel-Architektur, im Plan festgeschrieben)

- **Trigger statt Direkt-MR:** ServiceNow-Flow (IntegrationHub/REST) ruft nach Submit+Freigabe einen **GitLab Pipeline-Trigger** (Trigger-Token) auf und übergibt `intake.json`. Ein **CI-Job** legt Branch an, committet den Contract und öffnet den **MR** via `glab`/GitLab-API. Vorteil: Branch-/Layout-Logik bleibt versioniert im Repo; ServiceNow muss die Repo-Struktur nicht kennen.
- **Freigabe:** Governance-Approval (Dateneigner, DSB) in **ServiceNow** (erreicht Nicht-Git-Nutzer LHM-weit); der freigegebene Request setzt MR-Approval via API bzw. gibt den Merge frei. Technischer Merge in GitLab.
- **Hackathon-Abbildung:** `repository_dispatch` = Pipeline-Trigger; Action öffnet PR = CI öffnet MR; PR-Labels = ServiceNow-Approval-Stufen.

---

## Repo-Struktur (Datendomänen = Referate)

```
data-contracts-lhm/
├── README.md
├── docs/            architecture.md · governance.md · contributing.md
├── schemas/         odcs-v3.schema.json · intake.schema.json · lhm-rules.md
├── domains/
│   ├── mobilitaetsreferat/
│   │   ├── domain.yaml
│   │   └── data-products/radverkehr/
│   │       ├── data-product.yaml        # source.type: file_export · Port-Topologie
│   │       ├── contracts/
│   │       │   ├── input/opendata-raddaten.input.odcs.yaml
│   │       │   └── output/radverkehr-tageswerte.output.odcs.yaml
│   │       └── README.md                # auto-generierte Katalogseite
│   └── ewo/                             # Pilot-Produzent (Platzhalter)
│       ├── domain.yaml
│       └── data-products/.gitkeep
├── intake/          servicenow-catalog-item.md · example-intake.json
├── pipeline/
│   ├── ingest/      load_csv.py         # dlt: CSV → DuckDB (raw)
│   └── dbt/         dbt-duckdb-Projekt  # models/staging + models/mart + schema.yml (tests)
├── data/            kleines CSV-Sample / .gitkeep
├── scripts/         profile_source.py · intake_to_odcs.py · validate_odcs.py
│                    run_quality.py · ckan_publish.py · render_catalog.py
├── ckan/            docker-compose.yml  # lokale CKAN
└── .github/
    ├── ISSUE_TEMPLATE/new-data-contract.yml      # Fallback-Erfassung
    └── workflows/
        ├── intake-to-contract.yml    # intake.json → YAML → PR (+Labels)
        ├── validate-contracts.yml    # ODCS + LHM-Regeln
        ├── pipeline-and-quality.yml  # dlt → dbt → Quality (gegen materialisierte Daten)
        ├── approval-gate.yml         # owner/dsb-Freigabe (Labels)
        └── publish-ckan-catalog.yml  # nach Merge: CKAN + Katalog
```

**ODCS-v3-Kernfelder:** `apiVersion: v3.1.0`, `kind`, `id`, `version`, `status`, `name`, `domain`, `description{purpose,usage,limitations}`, `servers[]`, `schema[].properties[]` (`logicalType`, `physicalType`, `required`, `examples`, **`quality[]`**), `slaProperties[]`, `customProperties[]`.
**LHM-`customProperties`:** `classification`, `contract_status`, `personal_data`, `legal_basis`, `retention_period`, `dpo_notified`, `owner_approval`, `dpo_approval`, DCAT-Block (`license`, `spatial`, `accrual_periodicity`, `open_data_candidate`, `govdata_category`).

---

## Profiler: Contract aus Daten (Kern der Erleichterung)

`profile_source.py` liest die Quelle (Demo: CSV File-Export) und erzeugt einen **Draft-ODCS**:
- Spaltennamen, abgeleitete `logicalType`/`physicalType`, Nullable (aus Null-Quote)
- **Kandidaten-Quality-Regeln**: not-null (0 Nulls beobachtet), Wertebereiche (beobachtete min/max), Uniqueness (distinct==rows), abgeleitete Konsistenz (`gesamt = richtung_1 + richtung_2`)
- Freshness via `max(datum)`

Der Mensch bestätigt/ergänzt nur Governance-Felder (ServiceNow). `intake_to_odcs.py` merged Draft-Schema + Governance → finaler Contract.

---

## Pipeline + Quality Gate

- **Ingestion (dlt):** `pipeline/ingest/load_csv.py` lädt das CSV in eine DuckDB-`raw`-Tabelle (Materialisierung des **Input-Ports**).
- **Transformation (dbt-duckdb):** `models/staging` (Typcasts, `min-temp`→`min_temp`, Komma→Punkt) → `models/mart/radverkehr_tageswerte` (**Output-Port**). `schema.yml` enthält dbt-Tests (not_null, unique, accepted_range).
- **Quality Gate:** `run_quality.py` führt die **Contract-`quality`-Regeln** gegen die materialisierten DuckDB-Tabellen aus; zusätzlich `dbt test`. Verstoß → roter Check, blockt Merge. (LHM-Ziel: identische Regeln laufen produktiv auf Postgres via GitLab Runner.)

**Tooling (bewusst schlank):** `dlt`, `duckdb`, `dbt-duckdb`, `pyyaml`, `jsonschema`, `pandas`, `requests` (CKAN).

---

## CKAN-Integration (lokal, Docker)

Nach Merge: `publish-ckan-catalog.yml` → CKAN via `ckan/docker-compose.yml`; `ckan_publish.py` mappt ODCS → CKAN-Dataset + DCAT-AP.de-Extras (`license_id`, `spatial_uri`, `frequency`, `theme`) + LHM-Felder; `package_create`/`package_update`; nur `open_data_candidate: true`. `render_catalog.py` aktualisiert die Markdown-Katalogseite.

---

## Team-Aufteilung & 12-Stunden-Timeline (3 Personen)

**Stunde 0–1 — Kickoff (alle):** Konventionen, Domänenstruktur (`mobilitaetsreferat`/`ewo`), gemeinsam `intake.schema.json` **und** das Contract-Schema-Vokabular (Profiler↔Governance-Merge) fixieren. DuckDB/dbt-Projektgerüst anlegen. Danach Split.

| Workstream | Verantwortung | Kern-Deliverables |
| --- | --- | --- |
| **A — Domänen, Contracts & Profiler** | `domains/`-Struktur, `domain.yaml`, ODCS Input+Output (`radverkehr`) inkl. `quality`-Block, `templates`, `schemas/lhm-rules.md`, **`profile_source.py`** (CSV→Draft-ODCS), `docs/architecture.md`+`governance.md` | Beispielprodukt + Profiler + Regelwerk |
| **B — Intake, Governance, Validierung & Katalog** | `intake.schema.json`, `intake/servicenow-catalog-item.md` (+Topologie), **`profile.yml`-Workflow + Callback-Konzept** (Profiling→dynamisches Formular, s. [Workflow-Doc](workflow-intake-approval.md)), `intake_to_odcs.py` (Merge), `intake-to-contract.yml`, `approval-gate.yml` (Required-Checks-vor-Freigabe via Branch-Protection), Issue-Form-Fallback, `validate_odcs.py`+`validate-contracts.yml`, `ckan_publish.py`+`publish-ckan-catalog.yml`+`render_catalog.py` | Intake→PR→Freigabe→CKAN/Katalog |
| **C — Data Pipeline, Quality & Output Port** | `pipeline/ingest/load_csv.py` (dlt→DuckDB), `pipeline/dbt/` (staging+mart+Tests), `run_quality.py`, `pipeline-and-quality.yml`, **Output Port**: View `radverkehr_tageswerte` + Parquet/CSV-Export unter `output/`, **`apply_access.py`** (Contract→GRANTs/`access-policy.json`, s. [Access-Doc](access-and-output-port.md)), `ckan/docker-compose.yml` | Pipeline + Quality-Gate + bereitgestellter Output Port + Zugriffspolicy |

**Meilensteine:**
- **h3** — A: Profiler erzeugt Draft-ODCS aus CSV; B: intake.schema + Merge erzeugt Contract lokal; C: dlt lädt CSV→DuckDB, dbt-staging läuft.
- **h6** — Integration 1: PR aus `intake.json`; validate-Gate grün; dbt-mart `radverkehr_tageswerte` existiert.
- **h9** — Integration 2: quality-gate (Contract-Regeln + dbt-Tests) im PR; approval-gate über Labels; lokale CKAN nimmt `package_create`.
- **h11** — End-to-End: Quelle → Profiler+Formular → PR → alle Gates grün → Freigabe → Merge → CKAN aktualisiert → Katalog gerendert.
- **h11–12** — Demo-Skript, README-Diagramm, GitLab/ServiceNow-Portierungsnotizen.

**Descoping-Reihenfolge (falls Zeit knapp — End-to-End-Demo schützen):**
1. CKAN real → durch Mock/Log ersetzen (Mapping bleibt sichtbar).
2. dbt-Tests → nur Contract-`run_quality` behalten.
3. Profiler-Tiefe reduzieren (nur Spalten/Typen, Quality-Regeln manuell).
4. ServiceNow-Doku knapp halten (Topologie-Diagramm reicht).
Der **rote Faden Quelle→Contract→Pipeline→Merge→Katalog** wird nie geopfert.

---

## GitLab-/LHM-Portabilität

| Hackathon (GitHub) | LHM-Ziel |
| --- | --- |
| GitHub Actions | `.gitlab-ci.yml` auf **GitLab Runnern** |
| `repository_dispatch`/Issue-Form | **ServiceNow** → GitLab Pipeline-Trigger → CI öffnet MR |
| PR-Labels für Freigabe | **ServiceNow-Approval** (Dateneigner, DSB) |
| dlt → **DuckDB**, dbt-duckdb | dlt → **PostgreSQL**, dbt (gleiche Modelle/Tests) |
| CSV File-Export-Connector | zusätzlich `reporting_db`/`eai`-Connectoren |
| lokale CKAN (Docker) | **LHM-CKAN** + `ckanext-dcat` → GovData |

Repo-Layout, ODCS-Contracts, dbt-Modelle und Skripte sind weitgehend CI-agnostisch — Portierungsaufwand v.a. in Workflow-Definitionen, Connectoren und Warehouse-Target.

---

## Verification (End-to-End-Demo)

1. **Quelle→Draft:** `profile_source.py` auf CSV → Draft-ODCS mit Schema + Kandidatenregeln.
2. **Intake:** `example-intake.json` (Governance) → `intake-to-contract.yml` öffnet PR mit fertigem Contract + Labels.
3. **Negativtests:** (a) `open_data_candidate: true` ohne `license` → validate rot. (b) manipulierte Daten `gesamt ≠ richtung_1+richtung_2` → quality-gate rot. (c) `personal_data: true` ohne `dsb-approved` → approval-gate rot.
4. **Positivlauf:** korrigieren → dlt+dbt bauen `radverkehr_tageswerte`, alle Gates grün, Labels gesetzt → Merge.
5. **CKAN:** `publish-ckan-catalog` pusht Metadaten in lokale CKAN; Katalogseite aktualisiert.

---

## Bewusst außerhalb des Scopes (12 h)

- Weitere Connectoren (reporting_db/oracle/EAI) — Abstraktion vorbereitet, nur CSV implementiert.
- Echte ServiceNow-Instanz (Topologie dokumentiert, per Labels/Dispatch simuliert).
- Echte GovData-Publikation (lokale CKAN als Stellvertreter), Keycloak-Access-Control.
- MUCGPT-Intake (zugunsten ServiceNow zurückgestellt; andockbar).
