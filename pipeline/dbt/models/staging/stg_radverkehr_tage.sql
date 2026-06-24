-- Workstream C: Bereinigung Roh -> Staging.
-- TODO: Typcasts, 'min-temp'/'max-temp' -> min_temp/max_temp, Komma->Punkt bei Dezimalzahlen,
--       datum (YYYY.MM.DD) -> DATE.
select
    -- TODO: cast(replace(datum, '.', '-') as date) as datum,
    *
from {{ source('raw', 'raw_radverkehr_tage') }}
