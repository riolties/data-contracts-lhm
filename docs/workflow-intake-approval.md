# Workflow: Intake, Freigabe & Contract-Erzeugung (ServiceNow ↔ GitLab)

Dieses Dokument beschreibt den **Ende-zu-Ende-Workflow** zur Erzeugung und Freigabe eines Data Contracts. Leitprinzip: **Governance vor Technik** — die Frage „darf dieses Produkt existieren?" wird in ServiceNow geklärt, bevor GitLab auch nur einen Byte der Quelldaten anfasst. Erst nach vollständiger Freigabe wird GitLab einmalig getriggert.

## Rollen
- **Datenverantwortliche/r** (Antragsteller, oft = Data Steward): legt das Datenprodukt an, füllt das Formular manuell aus.
- **Dateneigner (Data Owner):** genehmigt fachlich/rechtlich (Stufe 1, immer).
- **Datenschutzbeauftragte/r (DSB):** genehmigt zusätzlich, wenn `personal_data: true` (Stufe 2).
- **Pipeline (GitLab Runner):** Contract-Bau, Validierung, dlt/dbt, Quality, CKAN. Läuft erst nach Freigabe.

## Kopplung SN ↔ GitLab (unidirektional)
- **SN → GitLab:** Pipeline-**Trigger-Token** (`POST /projects/:id/trigger/pipeline`) mit `intake.json`. ServiceNow kennt **kein** Repo-Layout — es feuert einmalig nach vollständiger Freigabe.
- **GitLab → SN:** Kein Pflicht-Rückkanal. Optional kann der CI-Job die MR-URL als Kommentar in den SN-Request schreiben; das ist Komfort, keine Architekturanforderung.

---

## Sequenz (4 Phasen)

```
Datenverantwortliche/r        ServiceNow (SN)                 GitLab (CI/Runner)
        │                          │                                  │
 (1) Formular ausfüllen ────────►  │                                  │
        │   Spalten + Typen,       │                                  │
        │   Klassifizierung,       │                                  │
        │   Rechtsgrundlage,       │                                  │
        │   Owner, Open-Data …     │                                  │
        │                          │                                  │
        │                   (2) FREIGABE                               │
        │                   Stufe 1: Dateneigner                       │
        │                   Stufe 2: DSB (nur personal_data)           │
        │                          │                                  │
        │                          │ (3) Freigabe → Trigger ────────► │
        │                          │   {intake.json}        intake_to_odcs.py
        │                          │                        → Branch + Commit
        │                          │                        → MR öffnen
        │                          │                                  │
        │                          │            (4) TECHNISCHE GATES (auf MR)
        │                          │                 validate-contracts
        │                          │                 pipeline-and-quality
        │                          │                 (dlt → dbt → Quality)
        │                          │                                  │
        │                          │                   Gates grün → Auto-Merge
        │                          │                        Merge → main
        │                          │                        publish-ckan-catalog
```

---

## Phasen im Detail

### (1) Formular ausfüllen
Datenverantwortliche/r öffnet das ServiceNow-Katalog-Item „Neues Datenprodukt" und füllt die **Governance-Felder** aus: CSV-Pfad (`source.location`), fachliche Beschreibung, Klassifizierung, Rechtsgrundlage (wenn `personal_data=true`), Open-Data-Flag, Lizenz, Owner.

**Spalten und Typen werden nicht eingetragen** — die zieht der Profiler automatisch aus der CSV nach Freigabe. Das ist governance-seitig sauber: Datenzugriff findet erst nach Freigabe statt.

### (2) Freigabe in ServiceNow
SN startet den Approval-Flow direkt nach Submit:
- **Stufe 1 – Dateneigner:** genehmigt fachlich/rechtlich (immer erforderlich).
- **Stufe 2 – DSB:** nur wenn `personal_data: true`; prüft Rechtsgrundlage, Aufbewahrung.

Jede Genehmigung ist auditierbar (DSGVO Art. 30). Bis zur vollständigen Freigabe passiert **nichts** in GitLab.

### (3) Einmaliger Trigger nach Freigabe (SN → GitLab)
Nach vollständiger Freigabe triggert SN die GitLab-Pipeline mit `intake.json` (enthält nur Governance-Felder + CSV-Pfad). Der CI-Job:
1. führt `profile_source.py` auf der CSV aus → Spalten, Typen, Quality-Kandidaten
2. führt `intake_to_odcs.py` aus → merged Profiler-Output + Governance → finaler ODCS-Contract + `data-product.yaml`
3. legt Branch an, committet, öffnet den MR

### (4) Technische Gates (GitLab, auf dem MR)
Als **Required Checks** laufen:
1. `validate-contracts` — ODCS-Schema (jsonschema) + LHM-Regeln.
2. `pipeline-and-quality` — dlt lädt Daten → dbt baut Mart → `run_quality.py` prüft Contract-`quality`-Regeln + `dbt test`.

Diese Gates sind ein **Sicherheitsnetz**, keine Governance. Scheitert ein Gate, bleibt der MR offen — der Antragsteller korrigiert die Implementierung (z.B. falsche Quality-Schwelle im Formular). Eine erneute SN-Freigabe ist nicht nötig, weil sich die Governance-Entscheidung nicht geändert hat. Gates grün → Auto-Merge → `publish-ckan-catalog`.

---

## Reihenfolge — Kurzfassung
**Formular (manuell) → Freigabe Dateneigner → Freigabe DSB (falls DSGVO) → einmaliger Trigger → Contract/MR → technische Gates → Auto-Merge → Publish.**

Governance **immer vor** Datenverarbeitung. Technische Korrektheit ist orthogonal zur Governance-Entscheidung.

---

## Hackathon-Abbildung (GitHub, ohne SN-Instanz)
| Real (SN+GitLab) | Hackathon (GitHub) |
| --- | --- |
| SN-Katalog-Item (manuell ausfüllen) | `intake/example-intake.json` / Issue-Form |
| Freigabe Dateneigner in SN | Label `owner-approved` auf dem Intake-Issue |
| Freigabe DSB in SN | Label `dsb-approved` auf dem Intake-Issue (nur wenn `personal_data=true`) |
| SN triggert GitLab nach Freigabe | `intake-to-contract.yml` getriggert durch Approval-Labels auf Issue |
| CI öffnet MR via glab/API | `peter-evans/create-pull-request` Action |
| Technische Gates als Required Checks | Branch-Protection: `validate-contracts` + `pipeline-and-quality` |
| Auto-Merge nach Gates | Auto-Merge nach grünen Checks |

Die Reihenfolge wird **technisch erzwungen**: `intake-to-contract.yml` prüft, ob die erforderlichen Approval-Labels auf dem Issue gesetzt sind, bevor der PR geöffnet wird.
