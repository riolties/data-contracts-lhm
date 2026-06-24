# Contributing — neues Datenprodukt onboarden

> Stub — ausarbeiten.

## Weg über das Formular (Soll-Prozess)
1. ServiceNow-Katalog-Item „Neues Datenprodukt" (Demo: GitHub Issue mit Label `data-contract`).
2. Profiler leitet das Schema aus der Quelle ab; Formular wird dynamisch vorbefüllt.
3. Submit → Pipeline erzeugt Contract + öffnet PR.
4. Gates grün → Freigabe (Dateneigner, ggf. DSB) → Merge → Katalog/CKAN.

Siehe [workflow-intake-approval.md](workflow-intake-approval.md).

## Lokaler Entwickler-Loop
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/validate_odcs.py "domains/**/contracts/**/*.odcs.yaml"
```

## Konventionen
- Domänen/Produkte: lowercase, `-`/`_`. Contracts: `*.odcs.yaml`. Produkt-ID: `lhm:<domain>:<port>:<produkt>`.
- Jede Spalte braucht eine `description` (LHM-Regel R9).
- Branches/Commits klein halten; ein PR = ein Datenprodukt/Änderung.
