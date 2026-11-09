# Track B results — Gaia DR3 high-proper-motion harvest + vetting

Status: first full-sky high-PM harvest complete (2026-11-09/10 session).

## Harvest

- Query (identical in `aip_chunked.py` and `aip_parallel.py`):
  `SELECT source_id,ra,dec,pmra,pmdec,parallax,parallax_error,phot_g_mean_mag,phot_bp_mean_mag,phot_rp_mean_mag,bp_rp,ruwe FROM gaiadr3.gaia_source WHERE source_id BETWEEN lo AND hi AND (pmra*pmra+pmdec*pmdec) > 22500 AND phot_g_mean_mag < 20 AND parallax IS NOT NULL AND ruwe < 1.4`
  (|pm| > 150 mas/yr, G < 20, RUWE < 1.4, parallax measured)
- Source: gaia.aip.de sync TAP. source_id space [0, 7*2^60) split into 4096
  chunks (chunk i = ids [i*7*2^48, (i+1)*7*2^48 - 1]).
- Layout: the legacy single worker (`aip_chunked.py`) covered chunks 0..1862
  in ~86 min (~21 chunks/min, 2-4 s per chunk). It was killed and replaced by
  5 `aip_parallel.py` workers on ranges [1803,2262) [2262,2720) [2720,3178)
  [3178,3636) [3636,4096); chunks 1803..1862 deliberately overlap the legacy
  tail (dedupe at merge). Aggregate rate ~70 chunks/min (~3.3x single
  worker); all 5 workers finished with 0 failed chunks in ~34 min. Empty
  chunks from ~3513 on (DR3 source_id ceiling ~6.92e18 < 3513*7*2^48).
- Rows: 130,318 unique high-PM sources
  (results/chunks/merge_report.txt has per-file counts; 1,801 overlapping
  duplicates removed, 0 malformed lines). Note: the legacy output had a
  793 KB NUL-byte prefix and no header (pre-merge artifact); merge_chunks.py
  strips NULs and restores the canonical header, sorted by source_id.

## Exclusion sets (results/known/, built by build_known.py / download_known.sh)

- `gcns_sources.txt`: 331,312 ids — Gaia Catalogue of Nearby Stars
  (Smart+2021, VizieR I/364/gcns). NB: the GCNS main table is NOT in
  J/A+A/649/A6 (that catalog carries only supplementary tables table1c/
  table1r/progwd/table3/maglim/missing/hyacomb/distpdf). CFA VizieR spent the
  session in a Postgres outage ('metaviz@CFA' no connection); the working
  route was the G-VO mirror dc.g-vo.org TAP, table `gcns.main`, keyset-
  paginated (`SELECT TOP 19999 source_id FROM gcns.main WHERE source_id > N
  ORDER BY source_id`; G-VO caps sync at 20k rows and uses TOP, not LIMIT).
- `kirkpatrick2024_sources.txt`: 2,576 ids — Kirkpatrick+2024 20-pc census
  (J/ApJS/271/55 table4; ids extracted from the 'Gaia' column of the
  pre-downloaded `kirkpatrick2024_table4.csv`, stripping 'Gaia EDR3 ').
- `simbad_ucd_sources.txt`: 43,397 ids — SIMBAD otype IN (LM*,BD*,SD*,WD*)
  with a Gaia DR3 id, via simbad.cfa.harvard.edu sim-tap (GET works, POST
  returns HTTP 400; the ids table column is `ids`, not `id`).
- Kirkpatrick 2021 (J/ApJS/253/7): tablea1 carries NO Gaia source ids
  (CatWISE astrometry only) — its objects are covered by the SIMBAD otype
  set and the superseding 2024 census; no position fallback needed for v1.
- Dead routes (do not retry without cause): CDS Strasbourg unreachable,
  vizier.nao.ac.jp and vizier.china-vo.org time out, CFA /ftp/ paths 404.

## Vetting (scripts/vet.py; KNOWN_FILES now a dynamic results/known/*.txt glob)

- 130,318 harvest rows -> 62,389 excluded as known (47.9%) -> 1,385
  ultracool-dwarf-like candidates (bp_rp > 2.5 AND H = G + 5*log10(pm) > 16).
- results/candidates.csv holds the full local list (225 KB, over the 200 KB
  git budget); results/candidates_top500.csv (81 KB) is the git artifact.

## Candidates

- Top 20 by H: results/candidates_top20.md — dossiers with LS-DR9 cutout
  links, 5-arcmin SIMBAD + GCNS nearest-known cones, and an epoch-aware
  same-object test (a pre-Gaia designation offset matching pm*16 yr, i.e. the
  2000->2016 epoch drift).
- Headline finding: ALL top-20 are pre-Gaia known objects missing SIMBAD
  Gaia-DR3 cross-ids (nearest SIMBAD entry sits 8-13 arcsec away, exactly the
  pm*16yr epoch offset; three are literally in SIMBAD under their own
  "Gaia DR3 <id>" name). Example: #1 Gaia DR3 3264554308968041728 =
  ULAS J033350.84+001406.1 (BD*). So the top-H region is a recovery region;
  scripts/check_knownness.py is the epoch-aware exclusion prototype (v2).
- Epoch-aware sweep over the top 500 candidates
  (results/knownness_top500.json, 5' SIMBAD cones, nearest-match tolerance
  1.3 x pm*16yr): 416 same-object (pre-Gaia known, missing Gaia cross-ids)
  vs 84 possible-new. Ranks 1..~150 are pure recovery zone; possible-new
  rows appear from ~rank 150 and dominate by rank ~450. Top possible-new
  (H-ranked): 778994474926961152 (H=16.98, 248 pc, bp_rp 2.98),
  1296928326363004416 (H=16.93, 205 pc, bp_rp 2.66),
  5390732032963218560 (H=16.92, 164 pc, bp_rp 3.18 — nearest SIMBAD entry is
  a * star 0.76' away, worth a manual check), 5036731890598470912,
  1173260339417897344 — all faint (G ~19.9-20.0), red, fast, beyond the GCNS
  wall, with no same-object match. These are the discovery-space rows.
  Git artifact: results/knownness_possible_new.csv (the 84 possible-new
  rows with nearest-SIMBAD context; the full per-candidate JSON stays local
  and is regenerated by scripts/check_knownness.py).

## Reproducibility

- harvest: `python3 scripts/aip_parallel.py <outdir> <start_chunk> <end_chunk>` (xN)
- merge: `python3 scripts/merge_chunks.py` (report: results/chunks/merge_report.txt)
- exclusions: `bash scripts/download_known.sh`
- vetting: `python3 scripts/vet.py`
- dossiers: `python3 scripts/make_dossiers.py 20`
- knownness sweep: `python3 scripts/check_knownness.py 100`

## Next steps (v2)

1. Fold the epoch-aware same-object filter into vet.py (a SIMBAD positions
   dump for the candidate set, or per-candidate cones as in
   check_knownness.py, which is the working prototype).
2. Position-based exclusion for Kirkpatrick 2021 (tablea1 has CatWISE
   astrometry but no Gaia ids).
3. Colour-magnitude refine: use M_G vs bp_rp with the 100-200pc L-dwarf locus;
   the top-H tail currently mixes cool subdwarfs (SD*).
