# LHM-Pflichtregeln (über ODCS hinaus)

`validate_odcs.py` prüft jeden `*.odcs.yaml` zweistufig: (1) gegen `odcs-v3.schema.json` (jsonschema), (2) gegen die folgenden **LHM-Governance-Regeln**. Verstoß → roter `validate-contracts`-Check.

Die LHM-Felder liegen in `customProperties[]` (Liste aus `{property, value}`).

## Pflichtregeln

| # | Regel | Bedingung | Fehlermeldung (Beispiel) |
| --- | --- | --- | --- |
| R1 | `classification` gesetzt | immer | `classification fehlt (public\|internal\|confidential)` |
| R2 | `classification` ∈ {public, internal, confidential} | immer | `classification ungültig` |
| R3 | `contract_status` gesetzt | immer | `contract_status fehlt` |
| R4 | `personal_data` gesetzt (bool) | immer | `personal_data fehlt` |
| R5 | `legal_basis` **und** `retention_period` vorhanden | wenn `personal_data: true` | `personenbezogene Daten ohne Rechtsgrundlage/Aufbewahrungsfrist` |
| R6 | `dpo_notified: true` | wenn `personal_data: true` | `DSB nicht benachrichtigt` |
| R7 | `license` **und** `spatial` **und** `govdata_category` vorhanden | wenn `open_data_candidate: true` | `Open-Data-Kandidat ohne license/spatial/govdata_category` |
| R8 | `classification: public` | wenn `open_data_candidate: true` | `nur öffentliche Daten dürfen Open-Data-Kandidat sein` |
| R9 | jedes `schema[].properties[]` hat `description` | immer | `Spalte <name> ohne Beschreibung` |
| R10 | Output-Contract hat ≥1 `quality`-Regel | für Output-Ports | `Output-Port ohne Quality-Regeln` |

## Freigabe-Regeln (approval-gate, nicht validate)
- `owner-approved`-Label erforderlich (immer) → entspricht `owner_approval` in `customProperties`.
- `dsb-approved`-Label erforderlich, wenn `personal_data: true` → entspricht `dpo_approval`.
- Reihenfolge: `validate-contracts` + `pipeline-and-quality` müssen **grün** sein, bevor Freigabe zählt (Branch-Protection). Siehe [workflow-intake-approval.md](../docs/workflow-intake-approval.md).

## Hinweise zur Implementierung (Workstream B/C)
- Regeln als Liste von Funktionen `(contract: dict) -> list[str]` (Fehler) umsetzen — leicht testbar.
- `customProperties` als Dict zugänglich machen: `{cp["property"]: cp["value"] for cp in contract.get("customProperties", [])}`.
