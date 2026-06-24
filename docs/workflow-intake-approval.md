# Workflow: Intake, Profiling, Validierung & Freigabe (ServiceNow ↔ GitLab)

Dieses Dokument beschreibt den **detaillierten Ende-zu-Ende-Workflow** zur Erzeugung und Freigabe eines Data Contracts — die Interaktion zwischen **ServiceNow** (LHM-weiter, niederschwelliger Einstieg + Genehmigungen) und **GitLab** (versionierte Wahrheit + Automatisierung). Leitprinzip: **Maschine prüft vor Mensch** (Validierung & Quality vor Freigabe), und **das Profiling-Ergebnis steuert das Formular** (der Mensch tippt kein technisches Schema).

## Rollen
- **Datenverantwortliche/r** (Antragsteller, oft = Data Steward): legt das Datenprodukt an, pflegt Governance-Felder.
- **Dateneigner (Data Owner):** genehmigt fachlich/rechtlich (Stufe 1).
- **Datenschutzbeauftragte/r (DSB):** genehmigt zusätzlich, wenn `personal_data: true` (Stufe 2).
- **Pipeline (GitLab Runner):** Profiler, Contract-Bau, Validierung, dlt/dbt, Quality, CKAN.

## Kopplung SN ↔ GitLab (bidirektional)
- **SN → GitLab:** Pipeline-**Trigger-Token** (`POST /projects/:id/trigger/pipeline`) mit Variablen (Quell-Koordinaten bzw. `intake.json`). ServiceNow kennt **kein** Repo-Layout.
- **GitLab → SN:** **Callback** über eine **Scripted REST API**/Table-API in ServiceNow (CI-Job `curl`t Ergebnisse in den Request-Record): Profiling-JSON, CI-Status, MR-URL/-IID. Auth via Service-Account-Token (Keycloak/Basic).

---

## Sequenz (6 Phasen)

```
Datenverantwortliche/r        ServiceNow (SN)                 GitLab (CI/Runner)
        │                          │                                  │
 (0) Quelle anmelden ───────────►  │                                  │
        │                   Request angelegt                          │
        │                          │ (1) trigger PROFILING ─────────► │
        │                          │   {source coords}        profile_source.py
        │                          │                          → profiling.json
        │                          │ ◄──── callback: profiling.json ──┤
        │                   Form wird DYNAMISCH                        │
        │                   aus profiling.json gebaut                  │
 (2) Governance ausfüllen ──────►  │                                  │
        │   (Beschreibungen,       │                                  │
        │    Klassifizierung,      │                                  │
        │    Rechtsgrundlage…)     │                                  │
        │                          │ (3) trigger CONTRACT ──────────► │
        │                          │   {intake.json}        intake_to_odcs.py
        │                          │                        → Branch+Commit
        │                          │                        → MR öffnen
        │                          │ ◄──── callback: MR-URL/IID ──────┤
        │                          │                                  │
        │                          │            (4) AUTOMATISCHE GATES (auf MR)
        │                          │                 validate-contracts
        │                          │                 pipeline-and-quality (dlt→dbt→DQ)
        │                          │ ◄──── callback: CI-Status (✓/✗) ─┤
        │                          │                                  │
        │                   (5) WENN ✓: Approval-Flow                  │
        │                   Stufe 1 Dateneigner                        │
        │                   Stufe 2 DSB (nur personal_data)            │
        │                          │ (6) approved → API: merge MR ───► │
        │                          │                        Merge → main
        │                          │                        publish-ckan-catalog
        │                          │ ◄──── callback: Dataset-URL ──────┤
        │                   Request „Closed Complete"                  │
```

---

## Phasen im Detail

### (0) Quelle anmelden — Minimal-Request
Datenverantwortliche/r öffnet das ServiceNow-Katalog-Item „Neues Datenprodukt" und gibt **nur die Quelle** an: Domäne/Referat, Produktname, `source.type` (file_export/reporting_db/…) und Quell-Koordinaten (Pfad des File-Exports bzw. DB+Schema+Tabelle). Noch keine Schema-Eingabe.

### (1) Profiling (SN → GitLab → SN)
SN triggert die **Profiling-Pipeline** mit den Quell-Koordinaten. Der Runner führt `profile_source.py` aus und erzeugt `profiling.json`:
```jsonc
{
  "columns": [
    {"name": "datum", "logical_type": "date", "null_rate": 0.0, "unique_rate": 0.51},
    {"name": "gesamt", "logical_type": "integer", "min": 0, "max": 18342, "null_rate": 0.0}
    // …
  ],
  "candidate_quality": [
    {"rule": "not_null", "column": "datum"},
    {"rule": "range", "column": "bewoelkung", "min": 0, "max": 100},
    {"rule": "expression", "expr": "gesamt = richtung_1 + richtung_2"}
  ],
  "pii_suspect": [],            // Heuristik: name/adresse/geburtsdatum/email/…
  "freshness": {"column": "datum", "max": "2025-12-31"},
  "row_count": 365
}
```
GitLab **callbackt** `profiling.json` in den SN-Request.

### (2) Dynamische Governance-Erfassung (Kern der Frage „individuell je nach Profiler")
ServiceNow rendert das Formular **anhand `profiling.json`**:
- **Pro erkannter Spalte eine Zeile** (Name + erkannter Typ vorausgefüllt) in einem **Multi-Row Variable Set (MRVS)** → Datenverantwortliche/r ergänzt **fachliche Beschreibung** und **Spalten-Klassifizierung**.
- **PII-Verdacht** (`pii_suspect` nicht leer) → **Catalog Client Script/UI Policy** schaltet `personal_data=true` vor, macht **Rechtsgrundlage** + **Aufbewahrungsfrist** zu Pflichtfeldern und markiert die DSB-Freigabe als erforderlich.
- **Kandidaten-Quality-Regeln** werden als bestätigbare/abwählbare Liste angezeigt (Mensch kann Regeln deaktivieren oder Grenzen anpassen).
- Mechanik: profiling.json landet in (versteckten) SN-Variablen; **Client Scripts + UI Policies** lesen sie und blenden Felder/Pflichten **bedingt** ein. Genau hier „fragt ServiceNow individuell je nach Profiler-Ergebnis ab".

> **Degraded-Modus:** Ist die Quelle zur Antragszeit nicht erreichbar (kein Profiling), fällt das Formular auf manuelle Spalteneingabe zurück — gleicher `intake.json`-Output.

### (3) Contract-Erzeugung + MR (SN → GitLab)
Bei Submit baut SN `intake.json` (= Profiling-Draft **+** Governance) und triggert die **Contract-Pipeline**. `intake_to_odcs.py` merged beides zum finalen ODCS-Contract, committet auf einen Branch und öffnet den **MR**; Labels `needs-owner-approval` (+ `needs-dsb-approval` falls personal_data). MR-URL/IID per Callback zurück in den SN-Record.

### (4) Automatische Validierung & Quality — **VOR** der Freigabe
Auf dem MR laufen als **Required Checks**:
1. `validate-contracts` — ODCS-Schema (jsonschema) + LHM-Regeln (`lhm-rules.md`).
2. `pipeline-and-quality` — dlt lädt die Daten → dbt baut den Mart → `run_quality.py` prüft die **bestätigten Quality-Regeln gegen die materialisierten Daten** + `dbt test`.

CI-Status wird an SN zurückgemeldet. **Warum vor der Freigabe?** Ein Dateneigner/DSB soll nichts genehmigen, das technisch ungültig ist oder die zugesagte Datenqualität verfehlt — sonst wäre die menschliche Freigabe wertlos. Branch-Protection erzwingt: **rote Gates → Approval-Flow startet gar nicht / Merge blockiert.**

### (5) Freigabe (ServiceNow Approval) — nur bei grünen Gates
SN startet den Approval-Flow erst nach „CI grün":
- **Stufe 1 – Dateneigner:** sieht Profiling-Report, Quality-Report und MR-Diff im SN-Record; genehmigt/lehnt ab.
- **Stufe 2 – DSB:** nur wenn `personal_data: true`; prüft Rechtsgrundlage, Aufbewahrung, Pseudonymisierung.
Jede Genehmigung schreibt `owner_approval`/`dpo_approval` (Wer/Wann) — auditierbar (DSGVO Art. 30).

### (6) Merge + Publikation
Nach vollständiger Freigabe ruft SN die GitLab-API: setzt MR-Approval bzw. **merged** den MR. Merge auf `main` triggert `publish-ckan-catalog` → CKAN/Katalog. Dataset-URL zurück an SN → Request „Closed Complete".

---

## Reihenfolge — Kurzfassung
**Profiling → (dynamisches) Formular → Contract/MR → Validierung+Quality (Maschine) → Freigabe Dateneigner → Freigabe DSB (falls DSGVO) → Merge → Publish.**
Validierung **immer vor** Freigabe. Freigabe **immer vor** Merge.

---

## Hackathon-Abbildung (GitHub, ohne SN-Instanz)
| Real (SN+GitLab) | Hackathon (GitHub) |
| --- | --- |
| Quelle anmelden (Catalog Item) | `intake/example-intake.json` Stufe 0 / Issue-Form Teil 1 |
| Profiling-Trigger + Callback | Action `profile.yml` postet `profiling.json` als Artefakt/Issue-Kommentar |
| Dynamisches Formular | Issue-Form, dessen Felder aus `profiling.json` vorbefüllt werden (Konzept gezeigt) |
| Contract-Trigger → MR | `intake-to-contract.yml` öffnet PR |
| Validierung+Quality als Required Checks | Branch-Protection: `validate-contracts` + `pipeline-and-quality` required |
| ServiceNow-Approval | PR-Labels `owner-approved`/`dsb-approved` → `approval-gate` |
| SN merged via API | Auto-Merge nach grünen Checks + Labels |

Branch-Protection erzwingt die Reihenfolge **technisch**: Approval-Labels allein mergen nicht, solange die Checks rot sind.
