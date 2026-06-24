# ServiceNow-Katalog-Item → intake.json (Feld-Mapping & Topologie)

Dokumentiert, wie das ServiceNow-Katalogformular auf `schemas/intake.schema.json` abbildet und wie ServiceNow mit GitLab interagiert. Detaillierter Ablauf: [workflow-intake-approval.md](../docs/workflow-intake-approval.md).

## Topologie (Trigger + Callback, lose gekoppelt)
- **SN → GitLab:** ServiceNow-Flow ruft GitLab **Pipeline-Trigger-Token** (`POST /projects/:id/trigger/pipeline`) mit Variablen (`intake.json` bzw. Quell-Koordinaten). GitLab-CI öffnet den Merge Request.
- **GitLab → SN:** CI callbackt über eine **Scripted REST API** in den Request-Record (profiling.json, CI-Status, MR-URL).
- ServiceNow kennt **kein** Repo-Layout; Branch-/MR-Logik bleibt im Repo.

## Feld-Mapping (Catalog-Variable → intake.json)
| ServiceNow-Variable | intake.json | Pflicht | Hinweis |
| --- | --- | --- | --- |
| Referat (Choice) | `domain` | ✓ | Slug |
| Produktname | `product` | ✓ | `[a-z0-9_-]+` |
| Titel | `title` | ✓ | |
| Zweck/Nutzung/Grenzen | `description.*` | | |
| Dateneigner | `owner.data_owner` | ✓ | Approver Stufe 1 |
| Data Steward / Kontakt | `owner.data_steward`/`contact` | | |
| Klassifizierung (Choice) | `classification` | ✓ | public/internal/confidential |
| Aktualisierung | `update_frequency` | | ISO-8601 (P1D…) |
| Personenbezogen? (Toggle) | `personal_data` | | schaltet DSB-Pflicht + R5/R6 |
| Rechtsgrundlage | `legal_basis` | (✓ wenn PII) | |
| Aufbewahrung | `retention_period` | (✓ wenn PII) | P3Y… |
| Open-Data? (Toggle) | `open_data_candidate` | | |
| Lizenz / Kategorie / Spatial | `license`/`govdata_category`/`spatial` | (✓ wenn Open-Data) | |
| Quelle (Typ + Ort) | `source.type`/`source.location` | ✓ | file_export im Demo |
| Spalten (MRVS) | `columns[]` | ✓ | vom **Profiler** vorbefüllt, Mensch annotiert |
| Quality-Regeln (MRVS) | `quality_rules[]` | | vom **Profiler** vorgeschlagen, bestätigt |

## Dynamik (Profiler steuert das Formular)
`profiling.json` aus Phase 1 befüllt die MRVS-Spaltenliste und die Quality-Regeln vor; **Catalog Client Scripts / UI Policies** machen bei PII-Verdacht `personal_data`, `legal_basis`, `retention_period` zu Pflichtfeldern und markieren die DSB-Freigabe.

## Hackathon-Fallback
`.github/ISSUE_TEMPLATE/new-data-contract.yml` erzeugt dasselbe `intake.json` (siehe `intake.example.json`).
