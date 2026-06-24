-- Contract-Regel 'pk_eindeutig' (severity: error):
-- Primärschlüssel (datum, zaehlstelle) muss eindeutig sein.
-- Singular Test: liefert die Duplikat-Schlüssel (leer = bestanden).
select
    datum,
    zaehlstelle,
    count(*) as n
from {{ ref('radverkehr_tageswerte') }}
group by datum, zaehlstelle
having count(*) > 1
