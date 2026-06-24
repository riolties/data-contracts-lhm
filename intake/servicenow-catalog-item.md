# ServiceNow-Katalog-Item „Neues Datenprodukt" — Feld-Mapping & Topologie

Dokumentiert, wie das ServiceNow-Katalogformular auf `schemas/intake.schema.json` abbildet
und wie ServiceNow nach Freigabe GitLab triggert. Detaillierter Ablauf:
[workflow-intake-approval.md](../docs/workflow-intake-approval.md).

## Topologie (Governance-zuerst, unidirektional)

```
Datenverantwortliche/r
  → SN-Formular ausfüllen (Governance-Felder + CSV-Pfad)
  → Freigabe: Dateneigner [→ DSB wenn personal_data]
  → SN triggert GitLab einmal mit intake.json
        GitLab-Pipeline:
          1. profile_source.py  (CSV → profiling.json)
          2. intake_to_odcs.py  (profiling.json + intake.json → Contracts + PR)
          3. validate-contracts + pipeline-and-quality (Gates)
          4. Auto-Merge → publish-ckan-catalog
```

- **SN → GitLab:** `POST /projects/:id/trigger/pipeline` mit Variable `INTAKE_JSON`
- **Kein Rückkanal** erforderlich — Governance ist vor dem Trigger abgeschlossen

## Feld-Mapping (Catalog-Variable → intake.json)

| ServiceNow-Variable | intake.json-Feld | Pflicht | Hinweis |
| --- | --- | :---: | --- |
| Referat (Choice) | `domain` | ✓ | Lowercase-Slug |
| Produktname | `product` | ✓ | `[a-z0-9_-]+` |
| Titel | `title` | ✓ | Anzeigename |
| Zweck | `description.purpose` | | Wozu dienen die Daten? |
| Nutzung | `description.usage` | | Wer nutzt sie wie? |
| Grenzen | `description.limitations` | | Was ist nicht enthalten? |
| Dateneigner | `owner.data_owner` | ✓ | E-Mail; Approver Stufe 1 |
| Data Steward | `owner.data_steward` | | |
| Kontakt | `owner.contact` | | |
| Klassifizierung | `classification` | ✓ | `public` / `internal` / `confidential` |
| Aktualisierungsfrequenz | `update_frequency` | | ISO-8601: `P1D`, `P1M`, … |
| Personenbezogen? | `personal_data` | | Toggle; aktiviert DSB-Pflicht |
| Rechtsgrundlage | `legal_basis` | ✓ wenn PII | z.B. `Art. 6(1)(e) DSGVO` |
| Aufbewahrungsfrist | `retention_period` | ✓ wenn PII | ISO-8601-Dauer: `P3Y` |
| Open-Data-Kandidat? | `open_data_candidate` | | Toggle |
| Lizenz-URI | `license` | ✓ wenn OD | z.B. `https://www.govdata.de/dl-de/by-2-0` |
| Räumliche Abdeckung | `spatial` | ✓ wenn OD | GeoNames-URI für München |
| GovData-Kategorie | `govdata_category` | ✓ wenn OD | DCAT-Theme-URI(s) |
| Quelltyp | `source.type` | ✓ | `file_export` / `reporting_db` / … |
| Quellpfad / Connection | `source.location` | ✓ | CSV-Pfad im Demo |

**Spalten und Typen werden NICHT im Formular eingetragen** — der Profiler
(`profile_source.py`) zieht sie nach Freigabe automatisch aus der CSV.

## Freigabe-Logik (SN-Approval-Flow)

| Stufe | Wer | Wann |
| --- | --- | --- |
| Stufe 1 | Dateneigner (`owner.data_owner`) | Immer |
| Stufe 2 | Datenschutzbeauftragte/r (DSB) | Nur wenn `personal_data: true` |

Nach vollständiger Freigabe: SN triggert GitLab und schließt den Freigabe-Prozess.

## Hackathon-Simulation (GitHub, ohne echte SN-Instanz)

| Real (SN) | Hackathon (GitHub) |
| --- | --- |
| SN-Formular ausfüllen | `intake/intake.example.json` bearbeiten / Issue-Form |
| Freigabe Dateneigner | Label `owner-approved` auf Intake-Issue setzen |
| Freigabe DSB | Label `dsb-approved` auf Intake-Issue setzen |
| SN triggert GitLab | Label `owner-approved` triggert `intake-to-contract.yml` |
| Alternativ: `workflow_dispatch` | Intake-JSON als Input übergeben |

## Fallback: Issue-Form

`.github/ISSUE_TEMPLATE/new-data-contract.yml` erzeugt ein Intake-Issue mit
einem JSON-Code-Block, den `intake-to-contract.yml` automatisch extrahiert.
