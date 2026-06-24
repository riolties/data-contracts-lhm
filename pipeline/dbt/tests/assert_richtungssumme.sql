-- Contract-Regel 'richtungssumme' (severity: error):
-- gesamt muss exakt richtung_1 + richtung_2 sein.
-- Singular Test: liefert inkonsistente Zeilen (leer = bestanden).
select *
from {{ ref('radverkehr_tageswerte') }}
where gesamt <> richtung_1 + richtung_2
