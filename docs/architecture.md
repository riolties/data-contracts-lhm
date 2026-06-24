# Architektur — Domänen, Data Products & Ports

Übergreifender Kontext: [hackathon-plan.md](hackathon-plan.md). Reihenfolge Governance↔Technik: [governance.md](governance.md) · [workflow-intake-approval.md](workflow-intake-approval.md).

## Datendomänen = Referate
`domains/<referat>/` bildet die LHM-Referate ab (die 15 Referate sind im [Domänen-Katalog](../domains/README.md) mit Slug-Konvention gelistet). Jede aktive/pilotierte Domäne hat:
- `domain.yaml` — Owner/Steward, Status, Liste der Datenprodukte
- `data-products/<produkt>/` — je ein Datenprodukt

Demo-Domäne: `mobilitaetsreferat` (aktiv) mit Produkt `radverkehr`. `kreisverwaltungsreferat` (KVR) ist Pilot-Platzhalter für einen personenbezogenen Produzenten — geplantes Produkt `adressdaten` (produzierende Einheit: Amt für Einwohnerwesen/EWO; → DSB-Freigabe-Pfad).

## Data Product & Ports (Data Mesh)
Ein Datenprodukt (`data-product.yaml`) bündelt **Input-Ports** (Quellen) und **Output-Ports** (konsumierbare Interfaces). Jeder Port referenziert genau einen ODCS-Contract unter `contracts/`.

```
Quelle (file_export/        Input Port              Output Port            Konsument
 reporting_db/eai/…)   ┌──────────────┐   dlt    ┌──────────┐  dbt   ┌──────────────┐
   CSV/DB  ───────────►│ input-Contract│ ───────►│ raw (DuckDB)│ ────►│ output-Contract│──► View / Parquet / API / Open-Data
                       │  *.input.odcs │         │  staging    │      │ *.output.odcs │
                       └──────────────┘         └──────────┘      └──────────────┘
                          (Workstream A)          (Workstream C: pipeline/)        (Workstream C: Output Port)
```

- **Input Port** = Vertrag mit der Quelle: was kommt rein, in welcher (Roh-)Form. Im Demo: CSV-File-Export. Roh, unbereinigt — der Contract dokumentiert Quell-Eigenheiten (z.B. `uhrzeit_ende` mit `.`-Trenner) als `limitations`.
- **Output Port** = stabiler Vertrag mit Konsumenten: bereinigter dbt-Mart `radverkehr_tageswerte` (View im Hub) + Parquet/CSV-Export. Eine Zeile je Zählstelle und Tag (PK `datum + zaehlstelle`).

## Namenskonventionen
| Element | Konvention | Beispiel |
| --- | --- | --- |
| Domäne / Produkt | lowercase, `-`/`_` | `mobilitaetsreferat`, `radverkehr` |
| Contract-Datei | `<produkt>.input.odcs.yaml` / `<produkt>.output.odcs.yaml` | `radverkehr.input.odcs.yaml` |
| Contract-`id` | `lhm:<domain>:<port>:<produkt>` | `lhm:mobilitaetsreferat:output:radverkehr` |
| Mart/Objekt | `<produkt>_<granularität>` | `radverkehr_tageswerte` |

## ODCS-Contract
Pro Port ein `*.odcs.yaml` (ODCS v3.1.0). Pflicht-Kernfelder: `version, apiVersion, kind, id, status`. LHM-Governance liegt in `customProperties` (Klassifizierung, DSGVO, Open-Data). Vorlage: `templates/contract.template.odcs.yaml`; Validierungsregeln: [`schemas/lhm-rules.md`](../schemas/lhm-rules.md).

## Quality-Konvention (A definiert → C konsumiert)
Das vendored ODCS-Schema lässt unter `unevaluatedProperties: false` bei `quality` weder `sql.query` noch `library.metric` zu. Daher die **LHM-Konvention**: ODCS-Typ `text` (schema-valide, menschenlesbare `description`), die **maschinell ausführbare Regel** steht in `customProperties` als `engine` + Parameter. `run_quality.py` (Workstream C) liest sie und prüft gegen die materialisierten Daten.

| `engine` | Parameter | Bedeutung |
| --- | --- | --- |
| `sql` | `query`, `expect` | Query liefert Wert (i.d.R. Verstoßzahl); muss `expect` (meist 0) entsprechen |
| `not_null` | `column` | Spalte ohne Null |
| `range` | `column`, `min`, `max` | Werte im Bereich |
| `row_count_min` | `min` | mindestens `min` Zeilen |

Alle Parameter sind skalare Strings. Für Mehrspaltenbedingungen (z.B. PK-Uniqueness) wird `engine: sql` mit einer entsprechenden `query` verwendet — kein eigenständiger `unique`-Engine-Typ mit Listparametern.

### Mapping Profiler-Output → ODCS-Contract-Quality

`profile_source.py` emittiert Kandidaten-Quality-Regeln im flachen Format (`intake.schema.json → quality_rules`). `intake_to_odcs.py` (Schritt 2) übersetzt diese in die ODCS-`customProperties`-Konvention:

| Profiler `rule` | Profiler Parameter | ODCS `engine` | ODCS Parameter |
| --- | --- | --- | --- |
| `not_null` | `column` | `not_null` | `column` |
| `unique` | `column` | `sql` | `query: "SELECT count(*) FROM (SELECT {column} FROM {table} GROUP BY {column} HAVING count(*) > 1)"`, `expect: 0` |
| `range` | `column`, `min`, `max` | `range` | `column`, `min`, `max` |
| `expression` | `expr: "c = a + b"` | `sql` | `query: "SELECT count(*) FROM {table} WHERE NOT ({expr})"`, `expect: 0` |

`severity: error` blockt das Gate, `warning` meldet nur. Beispiel siehe [Output-Contract](../domains/mobilitaetsreferat/data-products/radverkehr/contracts/output/radverkehr.output.odcs.yaml).

## Profiler (Pipeline-Schritt 1 nach Freigabe)
`scripts/profile_source.py` ist der **erste Schritt der Post-Freigabe-Pipeline**: nach der Governance-Freigabe in ServiceNow liest es die CSV aus `source.location` und erzeugt `profiling.json` mit Spalten/Typen, Null-/Unique-Quoten, Kandidaten-Quality (not-null, range, unique, Summen-Konsistenz wie `gesamt = richtung_1 + richtung_2`) und Freshness (`max(datum)`). Der Datenverantwortliche tippt **keine Spalten** ins SN-Formular — die kommen automatisch aus der Quelle (Datenzugriff erst nach Freigabe). `intake_to_odcs.py` (Schritt 2, Workstream B) merged `profiling.json` + Governance-Felder zum finalen Contract. Siehe [Profiler-Rolle im Plan](hackathon-plan.md).

## Versionierung & Deprecation von Output-Ports
- Contract-`version` (SemVer): Patch = Doku/Quality-Schwellen, Minor = additive Spalten, **Major = Breaking** (Spalte entfernt/umbenannt/Typ geändert).
- Breaking Change → neuer Output-Port parallel; alter Contract `status: deprecated` mit Auslauf-SLA, danach `retired`. Konsumenten migrieren in der Übergangszeit.
