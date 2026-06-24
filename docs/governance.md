# Governance — Rollen & Freigabe

> Stub (Workstream A/B) — ausarbeiten. Detaillierter Ablauf: [workflow-intake-approval.md](workflow-intake-approval.md).

## Rollen
| Rolle | Aufgabe |
| --- | --- |
| Datenverantwortliche/r (Antragsteller) | legt Datenprodukt an, pflegt Governance-Felder |
| Dateneigner (Data Owner) | Freigabe Stufe 1 (fachlich/rechtlich) |
| Datenschutzbeauftragte/r (DSB) | Freigabe Stufe 2, wenn `personal_data: true` |
| Data Steward | operative Pflege von Contract/Qualität |

## Freigabe (Reihenfolge)
1. **Maschine zuerst:** `validate-contracts` + `pipeline-and-quality` müssen grün sein (Branch-Protection).
2. **Mensch danach:** Dateneigner (`owner-approved`) → DSB (`dsb-approved`, nur bei personenbezogenen Daten).
3. Merge → `publish-ckan-catalog`.

## Klassifizierung
`public | internal | confidential` (Contract-`customProperties`). Steuert Zugriffskontrolle ([access-and-output-port.md](access-and-output-port.md)) und Open-Data-Eignung.

## TODO (Workstream A/B)
- [ ] Branch-Protection-Regeln dokumentieren (Required Checks)
- [ ] Label-Konvention finalisieren (`owner-approved`, `dsb-approved`, `needs-*`)
- [ ] Mapping Labels ↔ ServiceNow-Approval-Stufen
