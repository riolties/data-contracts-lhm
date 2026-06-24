# CKAN — Open-Data-Katalog (Workstream C / Output Port)

Der CKAN-Katalog ist der **Open-Data-Output-Port** der Plattform: nur Datenprodukte
mit `classification: public` **und** `open_data_candidate: true` werden hier aus dem
Output-Contract veröffentlicht (→ Ziel: GovData/DCAT-AP.de). Look & Feel angelehnt an
[opendata.muenchen.de](https://opendata.muenchen.de).

## Live-Demo
- **Portal:** https://ckan.davb.dev (CKAN 2.11, deutsch)
- **Hosting:** DigitalOcean-Droplet `ckan-hackathon` (fra1), Setup via [ckan-docker](https://github.com/ckan/ckan-docker) + Caddy (TLS über Cloudflare-DNS). Provisioniert vom Homelab-Server `m1s` (`~/provision.sh`, DO-Token in `~/.ckan-do.env`).
- **Komponenten:** ckan · postgres · solr · redis · datapusher · caddy (Reverse Proxy).

`docker-compose.yml` in diesem Ordner ist die **lokale** Minimal-Variante für Entwicklung
ohne Server. Die Live-Demo nutzt das vollständige ckan-docker-Setup auf dem Droplet.

## Branding (München-Look)
Per CKAN-Admin-API (`config_option_update`, in DB gespeichert, überlebt Neustarts):
Titel „Open Data Portal München", deutsche Intro-/About-Texte, Custom CSS (schwarzer
Header, blauer Akzent `#1f6fb2`), Münchner-Kindl-Logo.
Deutsche Locale (`ckan.locale_default=de`) und Upload-Freigabe (CKAN 2.11 verlangt
explizite `ckan.upload.<typ>.mimetypes`) stehen in der `.env` des Droplets.

## Pipeline-Integration (Contract → CKAN)
```bash
export CKAN_API_KEY=<api-token>          # CKAN: Konto → API-Tokens
# Metadaten aus dem Output-Contract + bereinigte Daten publizieren:
python scripts/ckan_publish.py \
  --contract domains/mobilitaetsreferat/data-products/radverkehr/contracts/output/radverkehr.output.odcs.yaml \
  --ckan-url https://ckan.davb.dev --api-key "$CKAN_API_KEY" \
  --data-file output/radverkehr_tageswerte.csv
```
- `ckan_publish.py` mappt ODCS-Output → CKAN-Dataset inkl. DCAT-AP.de-Extras
  (license, spatial, frequency, theme, contract_id, classification), legt die
  Ziel-Organisation (= `domain`) bei Bedarf an und ist idempotent
  (create/update via `package_show`; bestehende Ressourcen-IDs bleiben stabil).
  **Ohne API-Key:** Dry-Run (nur Payload).
- Mit `--data-file` wird die bereinigte Output-Datei (dbt-Mart
  `radverkehr_tageswerte`) als CSV-Ressource hoch-/upgeladen → DataPusher füllt den
  Datastore → Tabellen-Vorschau (`datatables_view`).

### Demo-Kontext befüllen
`seed_demo.py` legt die Fachreferate als Organisationen an und erzeugt einige
plausible Demo-Datensätze, damit das Portal wie ein echtes Open-Data-Portal wirkt:
```bash
export CKAN_API_KEY=<api-token>
python ckan/seed_demo.py --ckan-url https://ckan.davb.dev
```

## CI — alles läuft in GitHub Actions
`.github/workflows/publish-ckan-catalog.yml` fährt nach Merge auf `main` (Änderungen
unter `domains/**`, `pipeline/**`, `data/**`) die komplette Strecke **in Actions**:
Ingestion (dlt) → Transformation (dbt-duckdb, Python 3.12) → Output-Port-Export →
`ckan_publish.py` (Metadaten + bereinigte CSV) → Render der Katalogseite.

Konfiguration:
- Repo-**Variable** `CKAN_URL` = `https://ckan.davb.dev`
- Repo-**Secret** `CKAN_API_KEY` = CKAN-API-Token

Ist das Secret nicht gesetzt, läuft der Publish-Schritt als Dry-Run (kein Fehler).
`pipeline-and-quality.yml` baut dieselbe Pipeline zusätzlich als PR-Gate inkl.
Quality-Checks (Python 3.12 — dbt/mashumaro unterstützt 3.13/3.14 noch nicht).
