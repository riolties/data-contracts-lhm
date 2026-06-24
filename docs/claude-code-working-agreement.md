# Claude Code — Working Agreement (Hackathon)

Spielregeln für 3 Personen, die parallel mit **Claude Code** an diesem Repo arbeiten (je ~$100 Credit, 12 h). Ziel: konfliktfrei parallel arbeiten und das Budget nicht verbrennen.

## Branches & PRs
- Jeder arbeitet auf **einem eigenen Branch**: `ws-a`, `ws-b`, `ws-c`.
- Klein und oft committen; **PR nach `main`** statt direkt pushen → der `validate`/`quality`-Gate-Effekt wird im PR sichtbar.
- Dateieigentum laut Workstream (siehe Issues #1/#2/#3) respektieren — so gibt es kaum Merge-Konflikte:
  - **A:** `domains/`, `scripts/profile_source.py`, `templates/`, `schemas/lhm-rules.md`, `docs/architecture.md`+`governance.md`
  - **B:** `intake/`, `scripts/intake_to_odcs.py`, `scripts/validate_odcs.py`, `scripts/ckan_publish.py`, `scripts/render_catalog.py`, `.github/`
  - **C:** `pipeline/`, `scripts/run_quality.py`, `scripts/apply_access.py`, `ckan/`, `data/`

## Stunde-0-Sync (alle, ~30 min) — VOR dem Split
Gemeinsam einfrieren, sonst driften die Streams auseinander:
1. **`schemas/intake.schema.json`** — Feldnamen/Pflichtfelder final. Das ist die zentrale Schnittstelle A→B und B→C.
2. **Contract-Feldkonvention** — wie `columns[]` + `quality_rules[]` aus dem Profiler (A) in `customProperties`/`schema[].properties[]` landen (B's `intake_to_odcs.py`) und wie C's `run_quality.py` den `quality`-Block liest.
3. **Demo-Slug** = `radverkehr`, Domäne = `mobilitaetsreferat` (steht schon).

Danach committen, alle ziehen `main`, dann Split.

## Modell- & Effort-Wahl (Budget-Hebel)
Preise pro 1M Tokens: **Opus 4.8 $5/$25**, **Sonnet 4.6 $3/$15**. Cache-Reads ~0.1×.
- **Default: Sonnet 4.6** fürs Implementieren der Stubs (gut spezifiziert, mechanisch). `/model sonnet`.
- **Opus 4.8** gezielt für harte Designentscheidungen/Debugging. Modell **zwischen Sessions** wechseln, nicht mitten drin (Modellwechsel invalidiert den Prompt-Cache).
- **Effort** für mechanische Arbeit auf `high`/`medium` statt `xhigh`.
- Aufgabe **vollständig im ersten Prompt** beschreiben (die Issues liefern das) → weniger Nachfass-Turns = weniger Output-Tokens.
- Repo klein halten / `.gitignore` beachten (`.venv`, `*.duckdb`, `pipeline/dbt/target/`) → Kontext billig, Caching greift.

## Lokales Setup (einmal pro Person)
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Integration & Descoping
- Integrationspunkte: A's Profiler-Draft → B's Merge → PR → C's Gates. Stubs erlauben unabhängiges Arbeiten; nicht aufeinander warten.
- Bei Zeitdruck gilt die **Descoping-Reihenfolge** aus dem [Plan](hackathon-plan.md) — der rote Faden Quelle→Contract→Pipeline→Merge→Katalog wird nie geopfert.

## Definition of Done (pro PR)
- `validate-contracts` grün (ODCS + LHM-Regeln).
- Falls Contracts/Daten betroffen: `pipeline-and-quality` grün.
- Freigabe-Labels gesetzt, wo der Flow es verlangt (`owner-approved`, ggf. `dsb-approved`).
