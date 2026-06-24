# Radverkehr Tageswerte München

> Datenprodukt der Domäne **mobilitaetsreferat** · ![Klassifizierung](https://img.shields.io/badge/Klassifizierung-public-brightgreen) ![Open_Data](https://img.shields.io/badge/Open_Data-ja-brightgreen)

**Zweck:** Tägliche Radverkehrszahlen je Dauerzählstelle inkl. Wetter.

**Nutzung:** Mobilitätsplanung, Monitoring, Open-Data-Veröffentlichung.

**Einschränkungen:** Nur Dauerzählstellen; Wetter aggregiert je Tag.

## Metadaten

| | |
|---|---|
| **Domäne** | mobilitaetsreferat |
| **Produkt-ID** | lhm:mobilitaetsreferat:radverkehr |
| **Status** | active |
| **Quelle** | `file_export` · `data/sample_radverkehr_tageswerte_2025_01.csv` |
| **Klassifizierung** | `public` |
| **Personenbezogen** | Nein |
| **Open Data** | ✅ Ja · [Lizenz](https://www.govdata.de/dl-de/by-2-0) |
| **GovData-Kategorie** | http://publications.europa.eu/resource/authority/data-theme/TRAN |
| **SLA frequency** | 1 d |
| **SLA retention** | 5 y |

## Ports

- **Input** `radverkehr-input` — Rohdaten Radverkehr Tageswerte München. → [`contracts/input/radverkehr.input.odcs.yaml`](contracts/input/radverkehr.input.odcs.yaml)
- **Output** `radverkehr-output` — Bereinigte Daten; dbt-Mart 'radverkehr_tageswerte'. → [`contracts/output/radverkehr.output.odcs.yaml`](contracts/output/radverkehr.output.odcs.yaml) (db_view, file_export)

## Schema — `radverkehr_tageswerte`

*Eine Zeile je Datensatz.*

| Spalte | Typ | Pflicht | Beschreibung |
|---|---|:---:|---|
| `datum` | `date` | ✓ | Zähltag (Quellformat YYYY.MM.DD). |
| `zaehlstelle` | `string` | ✓ | Name der Dauerzählstelle (z.B. Arnulf, Erhardt). |
| `richtung_1` | `integer` | ✓ | Gezählte Radfahrten in Richtung 1. |
| `richtung_2` | `integer` | ✓ | Gezählte Radfahrten in Richtung 2. |
| `gesamt` | `integer` | ✓ | Gesamtzahl Radfahrten am Tag (= richtung_1 + richtung_2). |
| `min_temp` | `number` | ✓ | Tagestiefsttemperatur in °C (Begleitwetter). |
| `max_temp` | `number` | ✓ | Tageshöchsttemperatur in °C (Begleitwetter). |
| `niederschlag` | `number` | ✓ | Niederschlagsmenge in mm (Begleitwetter). |
| `bewoelkung` | `integer` | ✓ | Bewölkungsgrad in Prozent (0–100, Begleitwetter). |
| `sonnenstunden` | `number` | ✓ | Sonnenscheindauer in Stunden (Begleitwetter). |

### Quality-Regeln

| Name | Engine | Beschreibung | Severity |
|---|---|---|:---:|
| `not_null_datum` | `not_null` | Spalte datum ohne Nullwerte. | error |
| `not_null_zaehlstelle` | `not_null` | Spalte zaehlstelle ohne Nullwerte. | error |
| `not_null_richtung_1` | `not_null` | Spalte richtung_1 ohne Nullwerte. | error |
| `range_richtung_1` | `range` | Spalte richtung_1 im Bereich 39–1878. | error |
| `not_null_richtung_2` | `not_null` | Spalte richtung_2 ohne Nullwerte. | error |
| `range_richtung_2` | `range` | Spalte richtung_2 im Bereich 15–1442. | error |
| `not_null_gesamt` | `not_null` | Spalte gesamt ohne Nullwerte. | error |
| `range_gesamt` | `range` | Spalte gesamt im Bereich 85–3320. | error |
| `not_null_min_temp` | `not_null` | Spalte min_temp ohne Nullwerte. | error |
| `range_min_temp` | `range` | Spalte min_temp im Bereich -6.2–4.1. | error |
| `not_null_max_temp` | `not_null` | Spalte max_temp ohne Nullwerte. | error |
| `range_max_temp` | `range` | Spalte max_temp im Bereich -0.8–16.6. | error |
| `not_null_niederschlag` | `not_null` | Spalte niederschlag ohne Nullwerte. | error |
| `range_niederschlag` | `range` | Spalte niederschlag im Bereich 0.0–15.7. | error |
| `not_null_bewoelkung` | `not_null` | Spalte bewoelkung ohne Nullwerte. | error |
| `range_bewoelkung` | `range` | Spalte bewoelkung im Bereich 0–100. | error |
| `not_null_sonnenstunden` | `not_null` | Spalte sonnenstunden ohne Nullwerte. | error |
| `range_sonnenstunden` | `range` | Spalte sonnenstunden im Bereich 0.0–8.3. | error |
| `gesamt___richtung_1___richtung_2` | `sql` | Ausdruck: gesamt = richtung_1 + richtung_2. | error |
| `unique_datum_zaehlstelle` | `sql` | Spaltenkombination datum, zaehlstelle eindeutig. | error |

## Input-Port (Rohdaten)

Quelle: `public` · Server: CSV File-Export

| Spalte | Typ | Pflicht |
|---|---|:---:|
| `datum` | `date` | ✓ |
| `uhrzeit_start` | `time` | ✓ |
| `uhrzeit_ende` | `string` | ✓ |
| `zaehlstelle` | `string` | ✓ |
| `richtung_1` | `integer` | ✓ |
| `richtung_2` | `integer` | ✓ |
| `gesamt` | `integer` | ✓ |
| `min-temp` | `number` | ✓ |
| `max-temp` | `number` | ✓ |
| `niederschlag` | `number` | ✓ |
| `bewoelkung` | `integer` | ✓ |
| `sonnenstunden` | `number` | ✓ |

---

*Generiert von `scripts/render_catalog.py` aus `data-product.yaml` + ODCS-Contracts.*
