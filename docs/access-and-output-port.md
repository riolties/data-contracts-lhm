# Output Port & Zugriffskontrolle

Wie ein Datenprodukt seine Daten **bereitstellt** (Output Port) und wie der **Zugriff** kontrolliert wird — contract-getrieben, GitOps-konform.

## Was ist der Output Port?
Der **Output Port** ist die *stabile, konsumierbare Schnittstelle* eines Datenprodukts — entkoppelt von der internen Verarbeitung (staging/raw). Ein Datenprodukt kann **mehrere** Output Ports (Access Ports) für verschiedene Konsumtypen haben. Der Output-ODCS-Contract beschreibt **Schema, SLA, Klassifizierung und `servers[]` (= wo/wie serviert wird)**.

```
Quelle ─dlt→ raw ─dbt(staging)→ ─dbt(mart)→  ┌─ OUTPUT PORT(s) ───────────────┐
                                              │ • DB-View (SQL)                │
                                              │ • Datei-Export (Parquet/CSV)   │
                                              │ • API (optional)               │
                                              │ • Open Data (CKAN/GovData)     │
                                              └────────────────────────────────┘
```

## Wo & wie werden Daten bereitgestellt?

### 1. Primär: View im analytischen Data-Mesh-Hub (PostgreSQL)
- Der dbt-**Mart** materialisiert pro Datenprodukt eine **eigene Schema-Konvention**: `dp_<domain>_<produkt>` (z.B. `dp_mobilitaetsreferat_radverkehr`).
- Der Output Port ist eine **stabile View** `radverkehr_tageswerte` in diesem Schema. Konsumenten (Analyst:innen via Metabase/Superset/R/SPSS, FME-Jobs) lesen ausschließlich die View — interne Modelle dürfen sich ändern, die View-Signatur (= Output-Contract-Schema) bleibt stabil/versioniert.
- Versionierung: Schemaänderungen = neue Contract-`version`; breaking changes → neue View (`_v2`) mit Deprecation-Frist im Contract (`status: deprecated`).

### 2. Datei-Export (Parquet/CSV)
- Für Batch-Konsumenten/FME/Laufwerks-Workflows schreibt ein Pipeline-Step den Mart zusätzlich als **Parquet/CSV** an einen definierten Ort (Objektspeicher/Laufwerk). Pfad steht im Contract-`servers[]`.

### 3. API (optional)
- Wenn App-Konsumenten existieren: dünner Read-Service oder CKAN-Datastore-API vor der View. Im Hackathon nicht implementiert.

### 4. Open Data (CKAN → GovData)
- Nur wenn `open_data_candidate: true` **und** `classification: public`: `ckan_publish.py` veröffentlicht Metadaten (+ DCAT-AP.de) nach CKAN → GovData. Kein Auth (öffentlich).

`servers[]`-Beispiel im Output-Contract:
```yaml
servers:
  - server: mesh-hub-postgres
    type: postgres
    description: Analytischer Hub, stabile View
    customProperties:
      - {property: database, value: mesh}
      - {property: schema,   value: dp_mobilitaetsreferat_radverkehr}
      - {property: object,   value: radverkehr_tageswerte}
  - server: export-objstore
    type: custom
    description: Parquet-Export für Batch/FME
    customProperties:
      - {property: format, value: parquet}
      - {property: path,   value: s3://lhm-dp/mobilitaetsreferat/radverkehr/}
```

---

## Zugriffskontrolle (contract-getrieben)

### Identität (Authentifizierung)
- **Keycloak (OIDC)** — gleicher IdP wie MUCGPT/Plattform. Menschen via SSO, Tools/Pipelines via **Service-Accounts** (Client-Credentials).

### Autorisierung (RBAC, aus dem Contract generiert)
Der **Contract ist die Control Plane**. Er deklariert Klassifizierung, erlaubte Konsumentengruppen und (bei sensiblen Daten) Spaltenbehandlung:
```yaml
customProperties:
  - {property: classification, value: internal}        # public|internal|confidential
  - {property: personal_data,  value: false}
roles:                                                  # ODCS-roles[] = Zugriffsrollen
  - role: read_dp_mobilitaetsreferat_radverkehr
    description: Lesezugriff Output Port
    access: read
    customProperties:
      - {property: keycloak_group, value: dp-radverkehr-consumer}
```
Daraus generiert ein Pipeline-Step (`apply_access.py`, Stretch) **deterministisch**:
- **PostgreSQL-Rolle + Grants:** `CREATE ROLE read_dp_..._radverkehr; GRANT USAGE ON SCHEMA dp_... ; GRANT SELECT ON dp_..._radverkehr.radverkehr_tageswerte TO read_dp_..._radverkehr;`
- **Keycloak-Group-Mapping:** Keycloak-Gruppe `dp-radverkehr-consumer` → DB-Rolle (via `pg_oidc`/JWT-Claim oder Sync-Job).

→ **Mitglied der Keycloak-Gruppe ⇒ SELECT genau auf diese eine View.** Access wird *aus dem Contract erzeugt*, nicht von Hand verwaltet (gleiche GitOps-Idee wie der Contract selbst).

### Sensible/personenbezogene Daten
- **Spalten-Klassifizierung** im Contract → der Mart **maskiert/pseudonymisiert** (z.B. SHA-256 von Bürger-IDs; Zuordnungstabelle bleibt im Quellsystem) **oder** column-level Grants.
- **Row-Level Security (RLS)** in PostgreSQL für mandanten-/bereichsbezogene Einschränkung, falls nötig.
- `personal_data: true` ⇒ DSB-Freigabe (siehe [Intake-Workflow](workflow-intake-approval.md)); Verarbeitung landet im Art.-30-Register.

### Zugriffs**antrag** (wer darf konsumieren?)
Zugriff ist nicht offen — er wird beantragt und **vom Dateneigner freigegeben**:
```
Konsument (anderes Referat)
   └─ ServiceNow „Zugriff auf Datenprodukt X" ──► Approval Dateneigner
                                                   (+ DSB falls personal_data)
        └─ approved → Keycloak-Gruppenmitgliedschaft hinzugefügt
                      (= GRANT wirksam) ; Eintrag auditierbar (Art. 30)
```
Der Output-Contract listet so über die Zeit seine **berechtigten Konsumenten** — Data Lineage + Zugriffshistorie an einem Ort.

---

## Hackathon-Demo (DuckDB, ohne Keycloak/Postgres-Server)
- **Output Port real zeigen:** dbt-duckdb-Mart `radverkehr_tageswerte` als DuckDB-**View** + zusätzlicher **Parquet/CSV-Export** unter `output/`.
- **Zugriffskontrolle deklarativ + generiert zeigen:** `apply_access.py` liest die `roles[]`/`classification` aus dem Contract und **erzeugt** die `GRANT`-Statements + ein `access-policy.json` (Keycloak-Group → Rolle → Objekt). Wir zeigen das **generierte Artefakt** (portabel auf echtes Postgres/Keycloak), ohne IdP/DB-Server in 12h aufzusetzen.
- **Open-Data-Pfad:** für `radverkehr` (`classification: public`, `open_data_candidate: true`) → CKAN-Publikation; kein Auth — der Kontrast „public vs. internal" wird so im selben Repo sichtbar.

## LHM-Portabilität
| Demo | LHM-Ziel |
| --- | --- |
| DuckDB-View + Parquet-Export | PostgreSQL-View im `dp_*`-Schema + Objektspeicher/Laufwerk |
| `apply_access.py` → GRANT-Skript/JSON | Ausführung gegen **PostgreSQL** + **Keycloak**-Gruppen |
| Klassifizierung im Contract | Masking/RLS/Pseudonymisierung produktiv im Mart |
| Zugriff per Label/Doku | **ServiceNow**-Zugriffsantrag → Keycloak-Gruppe |
