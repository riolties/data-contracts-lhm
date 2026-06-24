# Demo-Anleitung — Hackathon LHM Data Contracts

## Schnellstart (1 Befehl)

```bash
# aus dem Projektroot:
streamlit run demo/sn_mock.py
```

Browser öffnet sich automatisch auf http://localhost:8501

---

## Demo-Ablauf (Schritt für Schritt)

### Schritt 1 — Formular (ServiceNow-Simulation)
- Alle Felder sind mit dem **Radverkehr-Beispiel** vorausgefüllt
- Felder erklären: "Hier sieht der Datenverantwortliche nur Governance-Felder — **keine Spalten**"
- Spalten-Erklärung: "Der Profiler zieht sie automatisch nach Freigabe aus der CSV"
- `📋 Antrag einreichen` klicken

### Schritt 2 — Freigabe
- Zeigt den Governance-Prozess: **Dateneigner muss immer freigeben**
- Bei `personal_data = true`: **DSB muss zusätzlich freigeben**
- Pipeline-Button ist erst aktiv wenn alle nötigen Freigaben erteilt sind
- `✅ Als Dateneigner freigeben` → `🚀 Pipeline triggern`

### Schritt 3 — Pipeline (live)
- **Schritt 1:** `profile_source.py` — CSV analysieren, Spalten/Typen erkennen
- **Schritt 2:** `intake_to_odcs.py` — Governance + Profiling → ODCS-Contracts
- **Schritt 3:** `validate_odcs.py` — ODCS-Schema + LHM-Regeln R1–R10 ✅
- **Schritt 4:** `render_catalog.py` — README/Katalogseite generieren
- **Bonus:** CKAN dry-run — zeigt den fertigen DCAT-AP.de-Payload

### Schritt 4 — Ergebnis
- **Katalog / README** — vollständig generierte Produktseite mit Schema, Quality-Regeln, SLA
- **Output Contract** — ODCS YAML mit allen Spalten, Typen, Quality-Regeln
- **Input Contract** — Rohdaten-Contract
- **CKAN-Payload** — JSON für die CKAN-API
- **GitHub PR** — Command zum Triggern des echten Workflows (optional live zeigen)

---

## Optional: Echter GitHub PR

```bash
# Triggert intake-to-contract.yml Workflow auf GitHub:
gh workflow run intake-to-contract.yml \
  -f intake_json='{"domain":"mobilitaetsreferat","product":"radverkehr",...}'
```

## Optional: CKAN lokal starten

```bash
docker compose -f ckan/docker-compose.yml up -d
# CKAN läuft auf http://localhost:5000
```

---

## Was installiert sein muss

```bash
pip install streamlit pyyaml jsonschema pandas
```

Alles in `requirements.txt` enthalten.
