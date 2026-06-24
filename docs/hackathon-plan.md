# Hackathon-Plan: Data Contracts & Data Products als GitOps-Blueprint (LHM)

## Context

Die Landeshauptstadt München (DAICE + aufzubauendes Data Office) baut ein **Data Mesh**, in dem **Data Contracts die Governance-Grundlage** bilden. Datendomänen sind organisatorisch die **Referate**. Phase-1-Pilot laut interner Konzeption: **EWO (Amt für Einwohnerwesen)** als Produzent (Adressdaten) → **Mobilitätsreferat** als Konsument. Bestehender Ziel-Stack: PostgreSQL, dbt, dlt, Keycloak, CKAN + `ckanext-dcat`, DCAT-AP.de → GovData. Rollenmodell: **Datenverantwortliche/Dateneigner (Data Owner)**, **Data Steward**, **Datenschutzbeauftragte (DSB)**.

Ziel des Hackathons (3 Personen, 12 h): In einem **GitHub-Repo** (`riolties/data-contracts-lhm`) exemplarisch die **Domänen-, Contract- und Pipeline-Struktur** aufbauen, die 1:1 intern **auf GitLab** wiederverwendbar ist — inkl. **Data-Product-Topologie (Input-/Output-Ports)**, **ODCS-v3-Contracts**, **Freigabe-Workflow**, **Quality Gate** und **CKAN-Anbindung**.

**Bestätigte Festlegungen:**
- Standard: **ODCS (Bitol) v3.1.0** (vendored JSON-Schema).
- Repo-Struktur **nach Datendomänen = Referate** (`domains/<referat>/data-products/<produkt>/…`).
- **Intake: ServiceNow-Katalogformular** (kein LLM) → strukturiertes JSON → Pipeline erzeugt ODCS-YAML + PR.
- **Freigabe: ServiceNow** mehrstufig (Dateneigner; + DSB wenn `dsgvo: ja`). Im Hackathon **über PR-Reviews + Labels simuliert** (`owner-approved`, `dsb-approved`).
- **Quality Gate: leichtgewichtig Python/SQL** (duckdb/pandas) gegen echte Daten; deklariert im ODCS-`quality`-Block.
- **CKAN-Demo: lokale CKAN via Docker** — Contract gemerged → Metadaten in CKAN aktualisiert.
- Beispieldomäne: **Mobilitätsreferat / Datenprodukt „radverkehr"** auf Basis der offenen **Raddauerzählstellen** (opendata.muenchen.de, Lizenz dl-by-de/2.0). Passt zum Pilot, kein DSGVO-Risiko.

Outcome: Ein vorzeigbarer, GitLab-portabler **Contract-as-Code-Blueprint** mit einem voll durchgespielten Datenprodukt und dem kompletten Lebenszyklus Erfassung → Freigabe → Validierung → Quality → Katalog/CKAN.

---

## Lebenszyklus (Zielbild in einem Bild)

```
Datenverantwortliche/r
   │  füllt
   ▼
ServiceNow-Katalogformular ──(REST, intake.json)──► GitHub/GitLab Pipeline
                                                        │ intake_to_odcs.py
                                                        ▼
                                              PR mit *.odcs.yaml + data-product.yaml
                                                        │
                          ┌─────────────────────────────┼─────────────────────────────┐
                          ▼                             ▼                              ▼
                  validate-contracts            quality-gate (DQ)            approval-gate
                  (ODCS + LHM-Regeln)        (Python/SQL vs. Daten)   (Dateneigner + DSB falls DSGVO)
                          └─────────────────────────────┼─────────────────────────────┘
                                                        ▼  alle grün + Freigaben
                                                      Merge
                                                        │ publish-ckan-catalog
                                                        ▼
                                         CKAN (lokal/Docker) + DCAT-AP.de-Extras
                                         + gerenderte Katalogseite im Repo
```

Kein Mensch schreibt YAML von Hand; kein LLM im kritischen Pfad.

---

## LHM-Mapping: Datendomänen → Repo-Struktur

Top-Level `domains/` bildet die **Referate** ab. Jede Domäne enthält Datenprodukte; jedes Produkt hat eine Port-Topologie und ODCS-Contracts.

```
data-contracts-lhm/
├── README.md
├── docs/
│   ├── architecture.md          # Domänen-, Data-Product- & Port-Modell
│   ├── governance.md            # Rollen + Freigabe-Workflow (ServiceNow)
│   └── contributing.md          # Onboarding eines Datenprodukts
├── schemas/
│   ├── odcs-v3.schema.json      # offizielles ODCS-v3 JSON-Schema (vendored)
│   ├── intake.schema.json       # Schema des ServiceNow-Formular-Payloads
│   └── lhm-rules.md             # LHM-Pflichtregeln (DSGVO/DCAT) über ODCS hinaus
├── domains/
│   ├── mobilitaetsreferat/
│   │   ├── domain.yaml          # Domänen-Metadaten, Data Owner/Steward
│   │   └── data-products/
│   │       └── radverkehr/                       # voll ausgearbeitetes Beispiel
│   │           ├── data-product.yaml             # Port-Topologie
│   │           ├── contracts/
│   │           │   ├── input/opendata-raddaten.input.odcs.yaml
│   │           │   └── output/radverkehr-tageswerte.output.odcs.yaml
│   │           └── README.md                     # auto-generierte Katalogseite
│   └── ewo/                                       # Pilot-Produzent (Platzhalter)
│       ├── domain.yaml
│       └── data-products/.gitkeep
├── intake/
│   ├── servicenow-catalog-item.md  # Feld-Mapping ServiceNow → intake.json
│   └── example-intake.json         # Beispiel-Payload (Demo-Trigger)
├── scripts/
│   ├── intake_to_odcs.py        # intake.json → ODCS-YAML + data-product.yaml
│   ├── validate_odcs.py         # jsonschema (ODCS) + LHM-Regeln
│   ├── run_quality.py           # ODCS-quality-Block → duckdb/pandas-Checks
│   ├── ckan_publish.py          # ODCS → CKAN-Dataset (+ DCAT-AP.de-Extras)
│   └── render_catalog.py        # Contracts → Markdown-Katalog
├── ckan/
│   └── docker-compose.yml       # lokale CKAN-Instanz für die Demo
└── .github/
    ├── ISSUE_TEMPLATE/new-data-contract.yml   # Fallback-Erfassung (Demo)
    └── workflows/
        ├── intake-to-contract.yml    # intake.json → YAML → PR
        ├── validate-contracts.yml    # PR-Gate: ODCS + LHM-Regeln
        ├── quality-gate.yml          # PR-Gate: ausgeführte DQ-Checks
        ├── approval-gate.yml         # PR-Gate: owner/dsb-Freigabe (Labels)
        └── publish-ckan-catalog.yml  # nach Merge: CKAN + Katalog
```

**Konventionen:** Domänen-/Produktordner lowercase mit `-`/`_`; Contract-Dateien `*.odcs.yaml`; Produkt-ID `lhm:<domain>:<port>:<produkt>`. GitLab-Portierung später ohne Layout-Änderung.

---

## ODCS-Contract (v3) — Anatomie + LHM-Erweiterungen

Pro Port ein Contract. Genutzte ODCS-v3-Felder: `apiVersion: v3.1.0`, `kind: DataContract`, `id`, `version`, `status`, `name`, `domain`, `tenant`, `description{purpose,usage,limitations}`, `servers[]`, `schema[]` (mit `properties[]`: `logicalType`, `physicalType`, `required`, `description`, `examples`, **`quality[]`**), `slaProperties[]`, `team[]`, `customProperties[]`.

**LHM-`customProperties`** (über ODCS-Kern hinaus): `classification`, `contract_status`, `personal_data` (dsgvo ja/nein), `legal_basis` (z.B. Art. 6(1)(e) DSGVO), `retention_period` (z.B. `P3Y`), `dpo_notified`, `owner_approval`, `dpo_approval`, sowie DCAT-Block (`license`, `spatial`, `accrual_periodicity`, `open_data_candidate`, `govdata_category`).

**Quality (deklarativ)** im `schema[].properties[].quality` bzw. objektweit, z.B.:
- `gesamt = richtung_1 + richtung_2` (Konsistenz)
- `gesamt >= 0`, `bewoelkung` in [0,100] (Wertebereich)
- `datum` not null & eindeutig je Zählstelle (Vollständigkeit/Unik)

---

## Intake: ServiceNow-Formular → Pipeline

1. **ServiceNow-Katalog-Item** (`intake/servicenow-catalog-item.md` dokumentiert das Feld-Mapping): strukturierte Felder (Domäne/Referat, Produktname, Owner, Klassifizierung, Aktualisierungsrhythmus, Spalten/Typen, Rechtsgrundlage, `dsgvo` ja/nein, Open-Data ja/nein, …). Erreicht alle Fachbereiche, SSO, keine Git-Kenntnis nötig.
2. ServiceNow sendet bei Submit ein **`intake.json`** (validiert gegen `schemas/intake.schema.json`) per **REST** an die Pipeline (Hackathon: `repository_dispatch` / Issue-Form-Fallback liefert dasselbe JSON).
3. **`intake-to-contract.yml`** ruft `intake_to_odcs.py`: erzeugt `data-product.yaml` + `*.odcs.yaml` unter `domains/<referat>/…`, öffnet **PR** und setzt Labels (`needs-owner-approval`, bei `dsgvo: ja` zusätzlich `needs-dsb-approval`).

> Fallback/Demo ohne ServiceNow-Instanz: GitHub **Issue Form** erzeugt identisches `intake.json` → gleicher Pfad.

---

## Freigabe (ServiceNow real, Git simuliert)

**Ziel-Architektur:** ServiceNow-Flow nach PR-Erstellung — Stufe 1 **Dateneigner** genehmigt; wenn `personal_data: true`, Stufe 2 **DSB**. Genehmigung schreibt `owner_approval`/`dpo_approval` in den Contract zurück bzw. gibt den Merge frei.

**Hackathon-Simulation:** `approval-gate.yml` prüft am PR die Labels `owner-approved` (immer nötig) und `dsb-approved` (nur wenn Contract `personal_data: true`). Reviewer setzen die Labels stellvertretend für die ServiceNow-Genehmiger → grüner Gate-Check als Merge-Voraussetzung. So ist der reale Workflow 1:1 nachvollziehbar, ohne ServiceNow-Instanz.

---

## Quality Gate (leichtgewichtig Python/SQL)

`run_quality.py` liest die `quality`-Regeln aus dem Contract und führt sie mit **duckdb/pandas** gegen eine Stichprobe der echten opendata-CSV aus (im Repo als kleines Sample oder per Download im CI). Verstoß → roter Check, blockt Merge. `quality-gate.yml` triggert das auf jeden PR, der Contracts ändert. (Ziel-Architektur: dieselben Regeln laufen produktiv in dbt/Soda — der Contract bleibt Single Source of Truth.)

---

## CKAN-Integration (lokal, Docker)

Nach Merge auf `main` startet `publish-ckan-catalog.yml`:
1. `ckan/docker-compose.yml` bringt eine lokale CKAN-Instanz hoch (Demo).
2. `ckan_publish.py` mappt den **ODCS-Contract → CKAN-Dataset** (Titel, Notes, Owner, Tags) + **DCAT-AP.de-Extras** (`license_id`, `spatial_uri`, `frequency`, `theme`) und LHM-Felder (`classification`, `contract_status`); ruft die **CKAN-API** (`package_create`/`package_update`). Nur Produkte mit `open_data_candidate: true` werden publiziert.
3. `render_catalog.py` erzeugt/aktualisiert die Markdown-Katalogseite je Datenprodukt.

---

## Team-Aufteilung & 12-Stunden-Timeline (3 Personen)

**Stunde 0–1 — Kickoff (alle):** Konventionen fix, ODCS-Schema + Domänenstruktur (`mobilitaetsreferat`, `ewo`) anlegen, `intake.schema.json`-Felder gemeinsam festlegen (Schnittstelle zwischen allen Streams). Danach Split.

| Workstream | Verantwortung | Kern-Deliverables |
| --- | --- | --- |
| **A — Domänen & Contracts** | `domains/`-Struktur, `domain.yaml`, ODCS Input+Output für `radverkehr` inkl. `quality`-Block, `templates`, `schemas/lhm-rules.md`, `docs/architecture.md` + `governance.md` | voll ausgearbeitetes Beispielprodukt + Regelwerk |
| **B — Intake & Freigabe** | `intake.schema.json`, `intake/servicenow-catalog-item.md`, `intake_to_odcs.py`, `intake-to-contract.yml`, `approval-gate.yml` (Label-Simulation), Issue-Form-Fallback | funktionierender no-code Intake + Freigabe-Gate |
| **C — Quality & CKAN** | `validate_odcs.py` + `validate-contracts.yml`, `run_quality.py` + `quality-gate.yml`, `ckan_publish.py` + `ckan/docker-compose.yml` + `publish-ckan-catalog.yml`, `render_catalog.py` | grüne/rote Gates + CKAN-Demo + Katalog |

**Meilensteine:**
- **h3** — A: Beispiel-Contract + Quality-Regeln stehen; B: `intake.schema.json` final + Skript erzeugt YAML lokal; C: ODCS-Validator + erster DQ-Check lokal grün.
- **h6** — Integration 1: PR aus `intake.json` wird erzeugt; validate- + quality-Gate greifen im PR.
- **h9** — Integration 2: approval-gate über Labels; lokale CKAN nimmt `package_create` an.
- **h11** — End-to-End: Formular-JSON → PR → Gates grün → Freigabe-Labels → Merge → CKAN aktualisiert → Katalogseite gerendert.
- **h11–12** — Demo-Skript, README-Diagramm, `docs/`-Portierungsnotizen GitLab/ServiceNow.

---

## GitLab-/LHM-Portabilität (explizit dokumentieren)

| Hackathon (GitHub) | LHM-Ziel |
| --- | --- |
| GitHub Actions (`.github/workflows`) | `.gitlab-ci.yml`-Jobs |
| Intake-JSON via Issue-Form/`repository_dispatch` | **ServiceNow-Katalog-Item** → REST-Trigger der Pipeline |
| Freigabe via PR-Labels | **ServiceNow-Approval-Flow** (Dateneigner, DSB) |
| Quality in Python/duckdb im CI | gleiche Regeln in **dbt/Soda** produktiv |
| lokale CKAN (Docker) | **LHM-CKAN** + `ckanext-dcat` → GovData |
| `gh pr create` | `glab`/GitLab-API |

Repo-Layout, ODCS-Contracts und Skripte sind CI-agnostisch — Portierungsaufwand nur in Workflow-Definitionen und Konnektoren.

---

## Verification (End-to-End-Demo)

1. **Intake:** `intake/example-intake.json` (bzw. Issue-Form) lösen → `intake-to-contract.yml` öffnet PR mit korrektem `*.odcs.yaml` + Labels.
2. **Negativtests:** (a) Contract mit `open_data_candidate: true` ohne `license` → `validate-contracts` rot. (b) Sample mit `gesamt ≠ richtung_1+richtung_2` → `quality-gate` rot. (c) `personal_data: true` ohne `dsb-approved` → `approval-gate` rot.
3. **Positivlauf:** Felder/Labels korrigieren → alle Gates grün → Merge.
4. **CKAN:** `publish-ckan-catalog` pusht Metadaten in lokale CKAN → Dataset sichtbar/aktualisiert; Katalogseite im Repo erneuert.

Damit ist der komplette Contract-as-Code-Lebenszyklus inkl. Freigabe, Quality und CKAN ohne manuelles YAML demonstriert.

---

## Bewusst außerhalb des Scopes (12 h)

- Produktive dbt/dlt-Pipelines, PostgreSQL, Keycloak-Access-Control (nur referenziert).
- Echte ServiceNow-Instanz (Workflow dokumentiert + per Labels simuliert).
- Echte GovData-Publikation (lokale CKAN als Stellvertreter).
- MUCGPT-Intake (geprüft, zugunsten ServiceNow zurückgestellt; Architektur bleibt andockbar).
