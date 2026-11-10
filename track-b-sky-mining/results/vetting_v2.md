# Track B v2 — epoch-aware vetting of the UCD-like high-PM candidates

Status: complete (2026-11-10 session). Scripts: `scripts/vet2.py`
(epoch-aware sweep + survivor deep-vetting + finalize),
`scripts/apply_lit_checks.py` (LS-DR9 imagery + literature-note merge),
`scripts/render_git_csvs.py` (compact git renders of the output CSVs).

## Why v2 (recap of finding F-11)

Source-id exclusion (vet.py, v1) misses pre-Gaia recoveries: known high-PM
stars sit in SIMBAD under 2MASS/LSPM/NLTT/LHS names without a Gaia DR3
cross-id, displaced along the PM vector by pm x |epoch_catalog - 2016.0|.
v2 makes the position test epoch-aware and runs it over ALL 1,385
ultracool-dwarf-like candidates (bp_rp > 2.5, H = G + 5 log10(pm) > 16).

## Method (explicit per catalog)

Positions are propagated from the Gaia DR3 epoch 2016.0 both backward and
forward (`propagate()` in vet2.py; pmra already includes cos(dec)):

| catalog | position epoch | screen |
|---|---|---|
| Gaia DR3 (candidates) | 2016.0 | — |
| SIMBAD `basic` | stored at the measurement epoch (J2000-ish for pre-Gaia entries; matches v1's finding) | 5' cone around the **pre-Gaia (2000.0)** position, TOP 12 hits, ALL hits evaluated (not just nearest) |
| SIMBAD modern entries | 2016-2026 | 5' cone around the **present-day (2026.859)** position (survivors only; see redundancy note) |
| CatWISE2020 (IRSA) | 2015.5; pm in deg/yr | cone at the epoch-2015.5 position, radius max(8", 1.3 x pm x 0.5yr) |
| GCNS (dc.g-vo.org) | Gaia EDR3 epoch 2016.0 | 5' cone at the 2016.0 position (top-50 survivors) + id-based exclusion (already in vet.py; GCNS carries EDR3 ids so id exclusion is sufficient) |
| harvest self-match | 2016.0 | any OTHER harvest row (130,318) within 2.0" at the same epoch -> DUPLICATE |

SIMBAD match rules (first hit wins; all recorded):

1. `direct-name` — hit main_id ends with the candidate's source_id (a
   "Gaia DR3 <id>" SIMBAD entry whose otype is outside LM*/BD*/SD*/WD*, so
   the otype id-exclusion missed it);
2. `tol2000` — sep(hit, pos2000) < 1.3 x pm x 16 yr. Covers stored catalog
   epochs 1979.2-2016.0 (sep(hit,pos2000) = pm x |2000 - t|);
3. `tolNow` — sep(hit, posNow) < 1.3 x pm x 10.86 yr. Covers stored epochs
   2012.7-2026.86 (modern entries);
4. `corr-old` — PM-track projection for hits implying catalog epoch
   1950-1979.2 (old LHS/NLTT-era positions): perpendicular residual
   <= max(2", 0.12 x pm x 16yr). Weaker rule (~4"-wide corridor); matches
   downgrade confidence to C. Union of the four rules covers stored epochs
   1950-2026.9 with no gap.

Redundancy note: the whole 1979-2027 PM track spans <= 20.8" for this
harvest (max pm 775 mas/yr) — far inside one 5' cone (300"). The two cones
are therefore near-identical windows; phase B (present-day cone) re-tests
survivors explicitly, which is where the evidence matters.

Evidence discipline: every HTTP query is appended to
`results/vetting_v2_querylog.csv`; per-candidate query coverage (hit counts
per cone, ident result, WISE result, cutout status) is encoded in
`results/vetting_v2.csv` / `results/possible_new_final.csv`. Every query
construction is deterministic from `scripts/vet2.py`.

## Funnel (stage-by-stage)

| stage | rows | in | out |
|---|---|---|---|
| high-PM harvest (\|pm\|>150, G<20, RUWE<1.4) | 130,318 | — | — |
| UCD-like cut (bp_rp>2.5, H>16) — vet.py v1 | 1,385 | 130,318 | 128,933 |
| known by source-id (GCNS / Kirkpatrick24 / SIMBAD UCD otypes) | 1,385 | — | (already excluded in v1) |
| harvest self-match <= 2" at epoch 2016 (DUPLICATE) | 1,385 | 1,385 | 0 duplicates found (expected random coincidences ~0.004, so zero is consistent) |
| epoch-aware SIMBAD cone @ ep2000 (phase A) | 1,385 | 1,385 | 764 KNOWN / 621 POSSIBLE-NEW / 0 failed |
| — known by rule: tol2000 495, direct-name 266, tolNow 3 | | | |
| survivors: second cone @ present-day position (phase B) | 621 | 621 | 0 flips to KNOWN |
| survivors: SIMBAD ident 'Gaia DR3/EDR3 <id>' (phase C) | 621 | 621 | 0 ident entries |
| survivors top-50: IRSA CatWISE2020 @ ep2015.5 (phase E) | 50 | 50 | 49 matched, 1 no-match |
| survivors top-50: GCNS 5' cone @ ep2016 (phase D) | 50 | 50 | 0 within 10" |
| LS-DR9 imagery check (200px jpeg, /tmp only, not committed) | 621 | 621 | 310 ok / 310 no-coverage / 1 http-error |
| literature (web search per source_id, top-6 candidates) | 6 | 6 | 0 published mentions found |

**Validation against v1**: on the top-500 candidates v2 reproduces the v1
sweep exactly — 500/500 verdicts agree (v1: 416 same-object / 84
possible-new; first possible-new at rank 210 in both).

**Final classification of the 1,385**: 764 KNOWN (pre-Gaia or Gaia-named
SIMBAD entries), 0 DUPLICATE, 621 POSSIBLE-NEW, 0 failed lookups.

## Confidence classes (possible-new only)

- **A — high (39)**: margin >= 2x tolerance to the nearest non-matching
  SIMBAD hit in both cones; no SIMBAD ident entry; no GCNS source within
  10"; CatWISE2020 counterpart with consistent PM (0.5 < pm_cw/pm_gaia < 2);
  parallax S/N >= 5; bp_rp >= 2.6. All 39 sit in the top-50 by H (the only
  block with the full check set).
- **C — ambiguous (27)**: a non-matching SIMBAD hit within 2x tolerance
  (margin < 2: 2 rows), implied-epoch corridor match, CatWISE PM ratio
  < 0.5 or > 2 (1 row: 5036731890598470912, cw 112.9 vs gaia 245.3 mas/yr
  at 0.37" sep — possible binary/unresolved PM confusion, needs eyes), or
  parallax S/N < 5 (24 rows).
- **B — needs human eyes (555)**: everything else. Includes all survivors
  beyond H-rank 50, whose CatWISE/GCNS checks were skipped (see honest
  failures) — they passed both SIMBAD cones + ident but have no
  machine-verified WISE counterpart.

Funnel summary: 1385 -> 764 KNOWN -> 621 POSSIBLE-NEW -> (39 A / 555 B /
27 C). This is a candidate list, not a discovery claim: "possible-new"
means we checked (SIMBAD 5' x2 cones at both epochs, ident, id-sets,
2" harvest self-match, plus CatWISE/GCNS/imagery/literature where run) and
found nothing that identifies the object.

## Top shortlist (15 highest-H possible-new; positions in degrees)

| # | source_id | ra,dec (2016.0) | pm mas/yr | dist pc | G | bp_rp | W1-W2 | pm_cw/pm_gaia | conf |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 778994474926961152 | 167.41774, +43.81838 | 248.7 | 248.6 | 20.00 | 2.98 | 0.22 | 1.27 | A |
| 2 | 1296928326363004416 | 224.85124, +40.84244 | 246.4 | 205.3 | 19.97 | 2.66 | 0.14 | 1.16 | A |
| 3 | 5390732032963218560 | 166.40405, -39.29354 | 248.9 | 164.2 | 19.94 | 3.18 | 0.18 | 1.06 | A |
| 4 | 5036731890598470912 | 22.36902, -26.99689 | 245.3 | 232.1 | 19.93 | 2.56 | 0.12 | 0.46 | C |
| 5 | 1173260339417897344 | 221.91347, +7.57312 | 237.9 | 214.8 | 19.98 | 2.73 | 0.22 | 0.95 | A |
| 6 | 4271023510457216896 | 274.51398, -1.72541 | 235.9 | 203.7 | 19.99 | 2.57 | -0.09 | 1.15 | B |
| 7 | 2468119419256161024 | 17.49945, -13.68596 | 234.6 | 198.4 | 19.98 | 2.80 | 0.26 | 0.98 | A |
| 8 | 3717399923897977984 | 200.13449, +6.14869 | 246.7 | 186.2 | 19.87 | 3.09 | 0.20 | 1.08 | A |
| 9 | 2813361564957760896 | 352.03633, +14.11066 | 249.9 | 194.2 | 19.82 | 2.91 | 0.16 | 1.07 | A |
| 10 | 3485388058311031552 | 174.82361, -26.20504 | 246.3 | 176.9 | 19.84 | 2.61 | 0.17 | 1.26 | A |
| 11 | 4585911133706711680 | 274.30112, +27.00041 | 247.2 | 164.3 | 19.83 | 2.99 | 0.18 | 1.03 | A |
| 12 | 3280469941644771328 | 68.12800, +3.22232 | 231.0 | 224.3 | 19.97 | 2.57 | 0.16 | 1.13 | B |
| 13 | 324266972833697920 | 33.71218, +30.24742 | 248.9 | 213.1 | 19.76 | 3.00 | 0.30 | 1.16 | A |
| 14 | 4750308012051385472 | 46.70826, -48.24698 | 226.1 | 322.7 | 19.96 | 2.63 | 0.03 | 1.19 | A |
| 15 | 5908704676544845568 | 225.17401, -42.06370 | 230.1 | 319.2 | 19.93 | 2.51 | -0.24 | 0.82 | B |

Why they are interesting: all are red (bp_rp 2.5-3.2), faint (G 19.8-20.0),
fast (~230-250 mas/yr) with H 16.6-17.0, parallax-supported distances
135-350 pc — just beyond the GCNS 100 pc completeness wall — with no
SIMBAD object at any epoch along their PM tracks, no GCNS membership, and
CatWISE counterparts whose WISE proper motions corroborate the Gaia ones
(mostly within ~10-30%). W1-W2 = -0.1..+0.3 is consistent with late-M /
cool-subdwarf photospheres rather than clear L dwarfs; the cohort looks
like a real, previously-unlisted population of faint high-PM red sources —
candidate objects for spectroscopic follow-up.

Pre-Gaia positions (epoch 2000.0) for the shortlist are in
`results/possible_new_final.csv` (ra2000/dec2000) — pointing old imaging
(2MASS/SDSS) at those coordinates is the next confirmation step.

Dossier links (LS-DR9 cutouts; imagery was fetched to /tmp and visually
inspected for #1, #2, #5 — each shows a red point source at the position):

- #1 https://www.legacysurvey.org/viewer/jpeg-cutout?ra=167.41774&dec=43.81838&layer=ls-dr9&size=200
- #2 https://www.legacysurvey.org/viewer/jpeg-cutout?ra=224.85124&dec=40.84244&layer=ls-dr9&size=200
- #5 https://www.legacysurvey.org/viewer/jpeg-cutout?ra=221.91347&dec=7.57312&layer=ls-dr9&size=200

## Honest failure notes

- **Query-log clobber**: phase A/B/C/E per-query latency entries were
  written by their own processes and the final finalize run overwrote
  `results/vetting_v2_querylog.csv` with the phase-D GCNS entries only
  (flush was overwrite-mode; fixed to append in vet2.py before the final
  runs). Per-candidate query coverage survives fully in the output CSVs
  (simbad_hits_ep2000, simbad_hits_now, ident_check, wise_check,
  gcns_check columns) and every query is reconstructible from vet2.py;
  the committed log holds the 50 phase-D GCNS cone entries (re-queried
  fresh at 16:33-16:35 UTC) + subsequent queries.
- **CatWISE scope**: IRSA cone queries on catwise_2020 cost ~13 s each;
  CatWISE cross-matching was run for the top-50 survivors by H only. The
  remaining 571 survivors have wise_check=`skipped(rank>50)` — their
  confidence is capped at B.
- **IRSA CatWISE PM units**: `pmra/pmdec` arrive in deg/yr (x1000 = mas/yr).
  One top-50 object (5036731890598470912) has WISE PM 0.46x the Gaia PM at
  0.37" separation — kept as confidence C, flagged for human review.
- **LS-DR9 coverage**: 310 of 621 survivors have DR9 imaging at their
  2016.0 position (imagery fetched locally, never committed); 310 are
  blank tiles (no DR9 coverage — mostly deep-south), 1 http-error remains.
  A blank tile is "no coverage", not "no object".
- **Unreachable services** (unchanged from session start): CDS Strasbourg,
  vizier.nao.ac.jp, vizier.china-vo.org, CFA /ftp/. IRSA TAP and
  legacy-survey.org were verified reachable and used.
- **Literature search depth**: web search per Gaia source_id was run for
  the 6 top candidates (all negative, see `results/lit_check_notes.json`);
  the tail was NOT individually literature-searched — SIMBAD ident +
  position cones are the machine screen for those.
- **Kirkpatrick 2021 position fallback**: still not implemented
  (tablea1 has no Gaia ids; its objects are covered by the SIMBAD otype +
  epoch-aware position screens, which now test positions directly).

## Reproducibility

```
python3 scripts/vet.py                                   # 1,385 candidates from the 130k harvest
python3 scripts/vet2.py sweep        # phase A: 1,385 SIMBAD cones @ep2000
python3 scripts/vet2.py survivors    # phases B/C/E: cones @now + ident + CatWISE(top-50) + GCNS(top-50)
python3 scripts/vet2.py finalize     # confidence classes + full-fidelity CSVs
python3 scripts/apply_lit_checks.py  # LS-DR9 imagery check + literature-note merge + re-finalize
python3 scripts/render_git_csvs.py   # compact git renders (all rows kept)
```

Outputs: `results/vetting_v2.csv` (compact render of ALL 1,385 rows —
rank, source_id, status, conf, rule+match name, margin, query-coverage
counters) and `results/possible_new_final.csv` (the 621 survivors with
positions at 2016.0/2000.0/2026.86 and per-check evidence), rendered by
`scripts/render_git_csvs.py` to meet the 200 KB git budget while keeping
every row. Full-fidelity lab files (5-decimal positions everywhere, long
match names, CatWISE/GCNS/imagery strings) are kept locally as
`results/vetting_v2_full.csv` / `results/possible_new_final_full.csv` and
regenerated by `python3 scripts/vet2.py finalize` +
`python3 scripts/apply_lit_checks.py` from
`results/vetting_v2_state.json` (state + *_full.csv not committed).
Also committed: `results/lit_check_notes.json`,
`results/vetting_v2_querylog.csv` (phase-D GCNS entries — see honest
failure notes above for the A-E log loss).
