-- Contract-Regel 'nicht_negativ' (severity: error):
-- Zählwerte dürfen nicht negativ sein.
-- Singular Test: liefert verletzende Zeilen (leer = bestanden).
select *
from {{ ref('radverkehr_tageswerte') }}
where richtung_1 < 0 or richtung_2 < 0 or gesamt < 0
