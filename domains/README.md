# Datendomänen — Katalog

Im Data Mesh der Landeshauptstadt München sind die **Datendomänen die Referate**. Dieser Katalog ist die autoritative Liste der Domänen-Slugs; jede aktive/pilotierte Domäne hat ein eigenes Verzeichnis `domains/<slug>/` mit `domain.yaml` und `data-products/`.

Quelle der Referatsstruktur: [stadt.muenchen.de/rathaus/verwaltung](https://stadt.muenchen.de/rathaus/verwaltung.html) (15 Referate).

## Slug-Konvention
- lowercase, Worttrenner `-`, Umlaute ausgeschrieben (`ä→ae`, `ö→oe`, `ü→ue`, `ß→ss`).
- Slug = Referatsname; keine Kürzel als Verzeichnisname (Kürzel nur informativ in der Tabelle).

## Referate (15)
| Referat | Slug (`domains/<slug>/`) | Kürzel | Status |
| --- | --- | --- | --- |
| Mobilitätsreferat | `mobilitaetsreferat` | — | **active** (Demo `radverkehr`) |
| Kreisverwaltungsreferat | `kreisverwaltungsreferat` | KVR | **pilot** (geplant: `adressdaten`, personenbezogen) |
| Baureferat | `baureferat` | — | planned |
| Direktorium | `direktorium` | — | planned |
| Gesundheitsreferat | `gesundheitsreferat` | — | planned |
| IT-Referat | `it-referat` | — | planned |
| Kommunalreferat | `kommunalreferat` | — | planned |
| Kulturreferat | `kulturreferat` | — | planned |
| Personal- und Organisationsreferat | `personal-und-organisationsreferat` | POR | planned |
| Referat für Arbeit und Wirtschaft | `referat-arbeit-und-wirtschaft` | RAW | planned |
| Referat für Bildung und Sport | `referat-bildung-und-sport` | RBS | planned |
| Referat für Klima- und Umweltschutz | `referat-klima-und-umweltschutz` | RKU | planned |
| Referat für Stadtplanung und Bauordnung | `referat-stadtplanung-und-bauordnung` | PLAN | planned |
| Sozialreferat | `sozialreferat` | — | planned |
| Stadtkämmerei | `stadtkaemmerei` | — | planned |

> Nur `active`/`pilot`-Domänen haben bereits ein Verzeichnis. Weitere Referate werden bei Bedarf nach gleichem Muster angelegt (`domain.yaml` + `data-products/`).

## Eigenbetriebe / Regiebetriebe (außerhalb des Hackathon-Scopes)
AWM, Münchner Stadtentwässerung (MSE), it@M, Märkte München, Stadtgüter München, Münchner Kammerspiele, Städtische Friedhöfe/Bestattung/Forstverwaltung u.a. lassen sich später als eigene Domänen oder Sub-Domänen modellieren — gleiche Struktur.

## Eine Domäne anlegen
```bash
mkdir -p domains/<slug>/data-products
$EDITOR domains/<slug>/domain.yaml   # name, title, data_owner, data_steward, status, data_products[]
```
Felder/Konventionen: siehe [docs/architecture.md](../docs/architecture.md).
