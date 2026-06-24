-- Workstream C — Staging: Roh (VARCHAR) -> typisiert & normalisiert.
-- dlt hat die Spalten 'min-temp'/'max-temp' beim Laden bereits zu min_temp/max_temp
-- normalisiert. Hier folgen: Datumskonvertierung (YYYY.MM.DD -> DATE), Komma->Punkt
-- bei Dezimalzahlen (defensiv; Quelle nutzt z.T. '.') und die Typcasts gemäß
-- Input-/Output-Contract. uhrzeit_start/uhrzeit_ende sind konstant (ganzer Tag) und
-- werden nicht durchgereicht (siehe Output-Contract).
with raw as (
    select * from {{ source('raw', 'raw_radverkehr_tage') }}
)
select
    -- Quellformat YYYY.MM.DD -> ISO-DATE
    strptime(trim(datum), '%Y.%m.%d')::date                         as datum,
    trim(zaehlstelle)                                               as zaehlstelle,

    -- Zählwerte: Ganzzahlen
    cast(trim(richtung_1) as integer)                              as richtung_1,
    cast(trim(richtung_2) as integer)                              as richtung_2,
    cast(trim(gesamt)     as integer)                              as gesamt,

    -- Wetter-Begleitdaten: Dezimal (Komma->Punkt defensiv) bzw. Prozent-Ganzzahl
    cast(replace(trim(min_temp),     ',', '.') as double)         as min_temp,
    cast(replace(trim(max_temp),     ',', '.') as double)         as max_temp,
    cast(replace(trim(niederschlag), ',', '.') as double)         as niederschlag,
    cast(trim(bewoelkung) as integer)                             as bewoelkung,
    cast(replace(trim(sonnenstunden), ',', '.') as double)       as sonnenstunden
from raw
