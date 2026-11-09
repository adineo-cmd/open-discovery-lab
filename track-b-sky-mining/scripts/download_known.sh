#!/bin/bash
# download_known.sh — build known-object exclusion sets into results/known/.
# The heavy lifting is in build_known.py; this wrapper runs it and reports.
#
# Routes that WORKED on 2026-11-09/10 (keep these first):
#   GCNS main catalogue (331,312 ids):
#     - vizier.cfa.harvard.edu catalog I/364/gcns  (NOT J/A+A/649/A6 — that
#       catalog only carries supplementary tables table1c/table1r/progwd/
#       table3/maglim/missing; its /ftp/ paths 404 on CFA)
#     - MIRROR THAT WORKED: dc.g-vo.org TAP, table gcns.main, keyset-paginated
#       with "SELECT TOP 19999 source_id FROM gcns.main WHERE source_id > N
#       ORDER BY source_id" (G-VO caps sync at 20k rows; no LIMIT, use TOP)
#   Kirkpatrick 2024 20-pc census:
#     - exoplanetarchive.ipac.caltech.edu hosts the paper table as CSV
#       (kirkpatrick2024_table4.csv already fetched); ids extracted from the
#       'Gaia' column ("Gaia EDR3 <id>")
#   Simbad ultracool/subdwarf/WD otypes (43,397 ids):
#     - simbad.cfa.harvard.edu sim-tap/sync via GET (POST returns HTTP 400)
#       with "SELECT ... FROM basic AS b JOIN ids AS i ON i.oidref=b.oid
#       WHERE b.otype IN ('LM*','BD*','SD*','WD*') AND i.ids LIKE 'Gaia DR3 %'"
#       (note: ids table column is `ids`, not `id`)
#
# Routes that FAILED on 2026-11-09/10 (do not bother):
#   - vizier.cfa.harvard.edu: transient Postgres outage ('metaviz@CFA' no
#     connection) for hours; retry asu-tsv if you like
#   - vizier.nao.ac.jp, vizier.china-vo.org: connection timeouts
#   - CDS Strasbourg (cds.unistra.fr, cdsarc): unreachable from this host
#   - Kirkpatrick 2021 J/ApJS/253/7 tablea1: carries NO Gaia source ids
#     (CatWISE astrometry only) — its objects are covered by the Simbad
#     otype set and the (superseding) Kirkpatrick 2024 census
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
python3 -I "$HERE/build_known.py" "$@"
echo "exclusion sets in results/known/:"
wc -l "$HERE"/../results/known/*.txt 2>/dev/null || echo "  (none)"
