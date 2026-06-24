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

### Schritt 3 — Pipeline (live auf GitHub Actions)
Die Demo triggert nach der Freigabe **echt** den Workflow `intake-to-contract.yml` auf
GitHub (entspricht dem GitLab-CI-Trigger aus ServiceNow im Produktivbetrieb) und pollt
den Run live:
- **Profiler** (`profile_source.py`) — CSV analysieren, Spalten/Typen/Quality-Kandidaten
- **Contracts erzeugen** (`intake_to_odcs.py`) — Governance + Profiling → ODCS-Contracts
- **PR öffnen** (`create-pull-request`) — Branch `contract/<domain>/<produkt>`, Label `owner-approved`
- Live-Fortschritt (Jobs/Steps mit ✅/⟳/⏳) + Link zum Run und zum geöffneten PR

> Voraussetzung: `gh` ist authentifiziert (`gh auth status`) und hat Zugriff auf das Repo.
> Bei flakigem WLAN als Fallback einen vorab geöffneten PR / Screencast bereithalten.

### Schritt 4 — Ergebnis (Dateien vom PR-Branch)
- **Katalog / README** — generierte Produktseite (sofern auf dem Branch vorhanden)
- **Output Contract** — ODCS YAML mit allen Spalten, Typen, Quality-Regeln
- **Input Contract** — Rohdaten-Contract
- **CKAN-Payload** — `ckan_publish.py --contract … ` als Dry-Run (kein API-Key nötig)
- **GitHub PR** — Link zum echten, gerade geöffneten Pull Request

Die nachgelagerten Gates (`validate-contracts`, `pipeline-and-quality`) und der
CKAN-Publish nach Merge (`publish-ckan-catalog`) laufen auf dem PR bzw. auf `main`
in GitHub Actions — im Pitch über das echte CKAN-Portal (ckan.davb.dev) zeigen.

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
