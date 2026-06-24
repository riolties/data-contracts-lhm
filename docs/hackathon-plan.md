# Hackathon-Plan: Data Contracts & Data Products als GitOps-Blueprint (LHM)

## Context

David (DAICE, Landeshauptstadt München) treibt eine **Data-Mesh-Initiative** voran, in der **Data Contracts die Governance-Grundlage** bilden. Es existiert bereits ein reales `contract.yaml` (ODCS-nah, mit LHM-Custom-Fields `classification`, `sla_freshness`, `contract_status`), ein Stack (PostgreSQL, dbt, dlt, Keycloak, CKAN + `ckanext-dcat`) und eine DCAT-AP.de-Anbindung an GovData. Quellen liegen verstreut in Copilot-Konversationen, **nicht** als eigene Notizen.

Ziel des Hackathons (3 Personen, 12 h): In einem **GitHub-Repo** (`riolties/data-contracts-lhm`, aktuell leer) exemplarisch die **Verzeichnis- und Pipeline-Struktur** aufbauen, die später intern **auf GitLab** wiederverwendbar ist — inklusive **Data-Product-Topologie (Input-/Output-Ports)** und **ODCS-v3-Data-Contracts**.

**Entscheidende Festlegungen (vom User bestätigt):**
- Standard: **ODCS (Bitol) v3**.
- **Kein LLM-Agent.** Fachbereiche befüllen Contracts über ein **geführtes Formular** (GitHub Issue Form), der Rest läuft **vollständig über Pipelines/GitHub Actions** (Formular → YAML → Validierung → PR → Katalog). MUCGPT-Anbindung bleibt bewusst offen und später andockbar.
- Beispiel-Domäne: ein offener Datensatz von **opendata.muenchen.de** (z. B. Raddauerzählstellen — öffentlich, Zeitreihe, kein DSGVO-Risiko).

Outcome: Ein vorzeigbarer, GitLab-portabler **Contract-as-Code-Blueprint** mit einem voll durchgespielten Beispiel-Datenprodukt und einem no-code Onboarding-Pfad für Fachbereiche.

---

## Zielbild (Konzept in einem Satz)

> Ein Fachbereich beschreibt sein Datenprodukt in einem **geführten Formular**, eine **GitHub Action** erzeugt daraus ein ODCS-`contract.yaml` und öffnet einen **Pull Request**, die **CI validiert** den Contract gegen das ODCS-Schema + LHM-Regeln, nach Merge rendert eine Pipeline eine **Katalogseite** (Stretch: DCAT-AP.de-Export für GovData).

Kein Mensch schreibt YAML von Hand; kein LLM im kritischen Pfad.

---

## Repo-Struktur (der eigentliche Blueprint)

```
data-contracts-lhm/
├── README.md                       # Konzept, Onboarding-Anleitung, Diagramm
├── docs/
│   ├── architecture.md             # Data-Product- & Port-Modell erklärt
│   └── contributing.md             # Wie ein Fachbereich ein Datenprodukt onboarded
├── schemas/
│   ├── odcs-v3.schema.json         # offizielles ODCS-v3 JSON-Schema (vendored)
│   └── lhm-rules.md                # LHM-Pflichtfelder (DSGVO/DCAT) über ODCS hinaus
├── templates/
│   └── data-product.template.yaml  # Vorlage, von der Action befüllt
├── data-products/
│   └── radverkehr/                 # EIN voll ausgearbeitetes Beispielprodukt
│       ├── data-product.yaml       # Produkt-Deskriptor: Ports-Topologie
│       ├── contracts/
│       │   ├── input/  ...input.odcs.yaml   # Input-Port → Quelle (opendata)
│       │   └── output/ ...output.odcs.yaml  # Output-Port → Konsument-Interface
│       └── README.md               # auto-generierte Katalog-/Doku-Seite
├── scripts/
│   ├── form_to_yaml.py             # Issue-Form-Body → contract.yaml
│   ├── validate_odcs.py            # jsonschema gegen ODCS + LHM-Regeln
│   └── render_catalog.py           # Contracts → Markdown-Katalog
└── .github/
    ├── ISSUE_TEMPLATE/
    │   └── new-data-contract.yml   # GEFÜHRTES FORMULAR (kein YAML-Wissen nötig)
    └── workflows/
        ├── validate-contracts.yml  # PR-Gate: Schema + Regeln
        ├── form-to-contract.yml    # Issue-Form → YAML → PR
        └── publish-catalog.yml     # nach Merge: Katalog rendern (+ DCAT Stretch)
```

**Data-Product-Modell** (`data-product.yaml`): beschreibt **Input-Ports** (Upstream-Quellen, z. B. opendata-API/CSV) und **Output-Ports** (konsumierbare Interfaces, z. B. `radverkehr_tageswerte`-View). Jeder Port **referenziert einen ODCS-Contract** unter `contracts/`. Das ist die Data-Mesh-Topologie, die der User explizit will.

**ODCS-Contract** (`*.odcs.yaml`): `apiVersion`/`kind: DataContract`, `id`, `info` (title/description/owner/contact), `schema` (Felder + Typen), `servicelevels` (freshness/SLA), plus **LHM-Custom-Properties** (`classification`, `contract_status`, DSGVO: `retention_period`, `dpo_notified`, Rechtsgrundlage) und **DCAT-Block** (`license`, `spatial`, `accrual_periodicity`, `open_data.candidate`, `govdata_category`).

---

## Geführter Intake (ersetzt den Agenten)

1. **GitHub Issue Form** (`new-data-contract.yml`): strukturierte Felder (Produktname, Owner, Klassifizierung-Dropdown, Aktualisierungsrhythmus, Felder/Spalten, Rechtsgrundlage, Open-Data ja/nein …). Fachbereich klickt sich durch — kein YAML.
2. **Action `form-to-contract.yml`** (Trigger: Issue mit Label `data-contract`): `form_to_yaml.py` parst den Issue-Body, füllt `templates/data-product.template.yaml`, schreibt nach `data-products/<slug>/…`, öffnet automatisch einen **PR** und verlinkt das Issue.
3. **PR durchläuft die normale CI** (Validierung unten) — Mensch reviewt/merged.

> GitLab-Pendant später: Issue-Description-Templates + CI-Job per Issue-Webhook. Bewusst so gewählt, dass der Pfad portabel bleibt.

---

## CI/CD-Pipelines

- **`validate-contracts.yml`** (on: pull_request): `validate_odcs.py` prüft jede geänderte `*.odcs.yaml` per `jsonschema` gegen `schemas/odcs-v3.schema.json` **und** gegen LHM-Pflichtregeln (`lhm-rules.md`: z. B. `classification` gesetzt, bei `open_data.candidate: true` müssen `license`+`spatial`+`govdata_category` vorhanden sein, bei personenbezogenen Daten `retention_period`+`dpo_notified`). Fail → roter PR-Check.
- **`publish-catalog.yml`** (on: push to main): `render_catalog.py` erzeugt/aktualisiert `README.md` je Datenprodukt + Index — die „Datenkatalog"-Sicht.
- **Stretch `publish-catalog.yml`-Erweiterung**: DCAT-AP.de JSON-LD-Export für Produkte mit `open_data.candidate: true` (Mapping ODCS→DCAT-AP.de, Hamburg `fhh-data/reportdcat-ap.de` als Referenz).

**Tooling-Empfehlung:** bewusst minimal — Python `pyyaml` + `jsonschema` statt fragiler Spezial-CLIs, damit die CI im Hackathon robust läuft und 1:1 in GitLab-CI portierbar ist.

---

## Team-Aufteilung & 12-Stunden-Timeline (3 Personen)

**Stunde 0–1 — Kickoff (alle):** Repo-Konventionen, ODCS-v3-Schema vendoren, opendata-Datensatz final wählen, `data-product.yaml`-Modell + Beispiel-Slug festlegen. Danach Split.

| Workstream | Verantwortung | Kern-Deliverables |
| --- | --- | --- |
| **A — Architektur & Contracts** | Ordnermodell, Port-Topologie, ODCS-Template, **ein** voll ausgearbeitetes Beispiel (Input+Output-Port) auf opendata-Daten, `docs/architecture.md` | `data-products/radverkehr/*`, `templates/`, `schemas/lhm-rules.md`, Doku |
| **B — Geführter Intake** | Issue Form + `form_to_yaml.py` + `form-to-contract.yml` (Issue → PR) | funktionierender no-code Onboarding-Pfad |
| **C — CI/CD & Katalog** | `validate_odcs.py` + `validate-contracts.yml`, `render_catalog.py` + `publish-catalog.yml`, DCAT-Stretch | grüner/roter PR-Gate, gerenderter Katalog |

**Meilensteine:**
- **h4** — A: Beispiel-Contract steht; B: Form-Felder fix; C: Validator läuft lokal.
- **h8** — Integration 1: Validator greift im PR; Beispielprodukt valide.
- **h11** — Integration 2: Issue-Form → Action → PR → CI grün → Katalog gerendert (End-to-End).
- **h11–12** — Demo-Skript, README-Diagramm, GitLab-Portierungsnotizen in `docs/`.

---

## GitLab-Portabilität (explizit dokumentieren)

| GitHub (Hackathon) | GitLab (LHM später) |
| --- | --- |
| GitHub Actions (`.github/workflows`) | `.gitlab-ci.yml` Jobs |
| Issue Forms (`ISSUE_TEMPLATE/*.yml`) | Issue-Description-Templates + CI-Trigger |
| `gh pr create` in Action | `glab`/GitLab-API im CI-Job |
| Repo-Struktur, ODCS, Skripte | **unverändert übernehmbar** |

Skripte (`scripts/*.py`) und Repo-Layout sind CI-agnostisch — der Portierungsaufwand beschränkt sich auf die Workflow-Definitionen.

---

## Verification (End-to-End-Demo)

1. **Negativtest:** PR mit unvollständigem Contract (z. B. `open_data.candidate: true` ohne `license`) → `validate-contracts.yml` schlägt **rot** an.
2. **Positivtest:** Feld ergänzen → Check wird **grün**.
3. **Intake-Loop:** Issue-Form ausfüllen → `form-to-contract.yml` öffnet automatisch PR mit korrektem `*.odcs.yaml` → CI grün → Merge.
4. **Katalog:** nach Merge erzeugt `publish-catalog.yml` die aktualisierte Katalogseite des Datenprodukts.
5. **(Stretch)** DCAT-AP.de-JSON-LD wird für das Open-Data-Produkt erzeugt.

Damit ist der komplette Contract-as-Code-Lebenszyklus ohne Agent und ohne manuelles YAML demonstriert.

---

## Bewusst außerhalb des Scopes (12 h)

- Echte dbt/dlt-Pipelines oder PostgreSQL-Anbindung (nur referenziert, nicht gebaut).
- Echte MUCGPT-Integration (Architektur lässt späteres Andocken zu: Form-Felder = Agent-Slots).
- Keycloak/Access-Control, CKAN-Live-Publishing.
