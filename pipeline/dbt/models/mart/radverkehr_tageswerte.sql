-- Workstream C — Output Port: stabile, konsumierbare View.
-- Signatur = Output-Contract-Schema (radverkehr.output.odcs.yaml):
-- genau diese 10 Spalten in dieser Reihenfolge. Interne Spalten (uhrzeit_*,
-- dlt-Technik) werden nicht durchgereicht. Konsumenten lesen ausschließlich
-- diese View (siehe docs/access-and-output-port.md).
select
    datum,
    zaehlstelle,
    richtung_1,
    richtung_2,
    gesamt,
    min_temp,
    max_temp,
    niederschlag,
    bewoelkung,
    sonnenstunden
from {{ ref('stg_radverkehr_tage') }}
