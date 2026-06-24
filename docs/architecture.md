# Architektur — Domänen, Data Products & Ports

> Stub (Workstream A) — ausarbeiten. Übergreifender Kontext: [hackathon-plan.md](hackathon-plan.md).

## Datendomänen = Referate
`domains/<referat>/` bildet die LHM-Referate ab; jede Domäne hat `domain.yaml` (Owner/Steward) und `data-products/`.

## Data Product
Ein Datenprodukt (`data-product.yaml`) bündelt **Input-Ports** (Quellen) und **Output-Ports** (konsumierbare Interfaces). Jeder Port referenziert einen ODCS-Contract unter `contracts/`.

```
source ─Input Port──► [ dlt → raw → dbt staging → dbt mart ] ─Output Port──► Konsument
                          (pipeline/)                          (View/Datei/API/Open-Data)
```

## ODCS-Contract
Pro Port ein `*.odcs.yaml` (ODCS v3.1.0). LHM-Felder in `customProperties`. Vorlage: `templates/contract.template.odcs.yaml`. Regeln: `schemas/lhm-rules.md`.

## TODO (Workstream A)
- [ ] Port-Modell + Namenskonventionen final beschreiben
- [ ] Diagramm radverkehr (Input/Output) ergänzen
- [ ] Versionierung/Deprecation von Output-Ports
