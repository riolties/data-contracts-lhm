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
1. **Governance zuerst (ServiceNow):** Dateneigner (immer) → DSB (nur wenn `personal_data=true`). Frage: darf dieses Produkt existieren? Orthogonal zur technischen Korrektheit.
2. **ERST NACH Freigabe:** ServiceNow triggert GitLab einmal mit `intake.json`.
3. **Technische Gates auf dem MR (Sicherheitsnetz):** `validate-contracts` + `pipeline-and-quality`. Scheitert ein Gate, bleibt der MR offen — Antragsteller korrigiert die Implementierung; keine erneute Governance-Freigabe nötig.
4. Alle Gates grün → Auto-Merge → `publish-ckan-catalog`.

## Klassifizierung
`public | internal | confidential` (Contract-`customProperties`). Steuert Zugriffskontrolle ([access-and-output-port.md](access-and-output-port.md)) und Open-Data-Eignung.

## TODO (Workstream A/B)
- [ ] Branch-Protection-Regeln dokumentieren (Required Checks)
- [ ] Label-Konvention finalisieren (`owner-approved`, `dsb-approved`, `needs-*`)
- [ ] Mapping Labels ↔ ServiceNow-Approval-Stufen
