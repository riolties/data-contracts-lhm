-- Workstream C: Output Port — stabile, konsumierbare View.
-- Signatur = Output-Contract-Schema (radverkehr-tageswerte.output.odcs.yaml).
-- TODO: finale Spaltenauswahl/-benennung gemäß Output-Contract.
select
    *
from {{ ref('stg_radverkehr_tage') }}
