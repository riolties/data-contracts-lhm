-- Contract-Regel 'bewoelkung_range' (severity: warning):
-- Bewölkung soll im Bereich 0–100 % liegen. Als Warnung konfiguriert, damit ein
-- Ausreißer im Begleitwetter das Gate nicht hart blockt (entspricht severity:warning).
{{ config(severity='warn') }}
select *
from {{ ref('radverkehr_tageswerte') }}
where bewoelkung is not null
  and (bewoelkung < 0 or bewoelkung > 100)
