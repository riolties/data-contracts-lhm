# WORKLOG


## 2026-06-24 — CKAN-Integration (Workstream C, Output Port)
- Live-CKAN https://ckan.davb.dev (CKAN 2.11, DO-Droplet via ckan-docker + Caddy) im München-Look gebrandet: Titel „Open Data Portal München", deutsche Locale + Intro/About, Custom CSS (schwarzer Header, blauer Akzent), Münchner-Kindl-Logo (`config_option_update`); Upload-Mimetypes + `locale_default=de` in der `.env` des Droplets, ckan neu gestartet.
- 5 Fachreferate als Organisationen + 6 Demo-Datensätze angelegt (`ckan/seed_demo.py`).
- Pipeline-Integration end-to-end getestet: `scripts/ckan_publish.py` publiziert `radverkehr` aus dem Output-Contract (Dataset + DCAT-AP.de-Extras); bereinigter dbt-Mart als CSV-Ressource (`--data-file`) → Datastore + Tabellen-Vorschau.
- `ckan_publish.py` gehärtet: Authorization-Header (API-Token), Org-Auto-Anlage, Themes in ein Extra gejoint (CKAN erlaubt keine doppelten Extra-Keys), idempotenter Daten-Upload mit **stabilen Ressourcen-IDs** (bestehende Ressourcen werden in den `package_update`-Payload zurückgemergt, statt sie zu überschreiben).
- **Komplette Strecke läuft in GitHub Actions**: `publish-ckan-catalog.yml` baut auf `main` die Pipeline (dlt → dbt → Export) und publiziert Metadaten + Daten nach CKAN. Repo-Variable `CKAN_URL` + Secret `CKAN_API_KEY` (ohne Secret → Dry-Run). Doku: `ckan/README.md`.
- dbt-Build bestätigt lauffähig auf Python 3.11/3.12 (alle 9 Tests PASS); CI pinnt 3.12. Kein Workaround — das frühere Problem war nur lokales Python 3.14 (mashumaro unterstützt 3.13/3.14 noch nicht).

## 2026-06-24 15:36

## 2026-06-24 16:07

## 2026-06-24 16:17

## 2026-06-24 16:24

## 2026-06-24 16:26

## 2026-06-24 16:30
