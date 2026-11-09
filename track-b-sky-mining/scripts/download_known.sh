#!/bin/bash
# download_known.sh — pull known-object catalogs (CFA VizieR mirror) into
# results/known/ as plain source-id lists for vetting.
# Sources: GCNS (J/A+A/649/A6), Kirkpatrick 20pc BD census (J/ApJS/253/7),
# Kirkpatrick full 20pc census (J/ApJS/271/55).
# NB: CFA mirror had transient DB outages on 2026-11-09; retry as needed.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
K="$HERE/../results/known"
mkdir -p "$K"

fetch_tsv () {  # $1 = vizier cat path, $2 = output file, $3 = column with source id
  echo "fetching $1 ..."
  curl -sS -m 300 "https://vizier.cfa.harvard.edu/viz-bin/asu-tsv?-source=$1&-out=$3&-out.max=unlimited" -o /tmp/viz.tsv
  # VizieR TSV: '#' comments, header line, then rows. Extract the id column.
  awk -F'\t' 'BEGIN{n=0} /^#/{next} {n++; if(n==2){for(i=1;i<=NF;i++) if($i ~ /Source|Name/) c=i; next} if(c && $c ~ /^[0-9]+$/) print $c}' /tmp/viz.tsv > "$2"
  echo "  -> $(wc -l < "$2") ids"
}

fetch_tsv "J/A%2BA/649/A6/gcns"      "$K/gcns_sources.txt"           "Source"
fetch_tsv "J/ApJS/253/7/table1"      "$K/kirkpatrick2021_sources.txt" "Source"
fetch_tsv "J/ApJS/271/55/table1"     "$K/kirkpatrick2024_sources.txt" "Source"
echo "done."
