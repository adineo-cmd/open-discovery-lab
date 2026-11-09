# Track B — Sky Mining (public survey data)

**Mission:** find uncatalogued astronomical objects in public survey data,
with fully reproducible methodology and named candidate lists.

## Why this is viable

Backyard Worlds (May 2026): volunteers mining public WISE data found 3,006
uncatalogued ultracool dwarfs — doubling the known population. Public-data
mining finds things professional catalogs miss.

## Chosen niche (feasible on a 12-core box, no petabyte downloads)

**High-proper-motion, faint, red sources in Gaia DR3 not present in known
ultracool-dwarf catalogs.**

- Data source: [Gaia DR3](https://gea.esac.esa.int/archive/) via the TAP
  service (ADQL over HTTP — no bulk download).
- Method: PM ≥ 100 mas/yr, G ≤ 20, color cuts (BP−RP, and absolute
  magnitude via parallax), reduced-proper-motion ranking.
- Exclusion: cross-match against published ultracool-dwarf censuses
  (VizieR) and SIMBAD; survivors = candidates.
- Vetting: per-candidate dossier (images via legacy surveys cutouts,
  literature check), publish candidate table + rejection reasons.

## Deliverables

- `scripts/` — every query and cut, reproducible end-to-end.
- `results/candidates.csv` — vetted candidate list with evidence links.
- Journal entries for every vetting decision; paper draft when candidates
  stabilize.

## Follow-on niches (queue)

1. ZTF archival light curves: uncatalogued long-period variables in the
   galactic plane.
2. WISE motion pairs: faint common-proper-motion companions.
3. TESS: uncatalogued long-cadence eclipsing binaries.
