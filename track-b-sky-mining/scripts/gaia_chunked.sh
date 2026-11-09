#!/bin/bash
# gaia_chunked.sh — chunked high-PM harvest from Gaia DR3 on ESAC TAP.
# The anonymous async tier aborts jobs > 60 s; full-sky scans don't fit.
# source_id is the primary key: BETWEEN-ranges hit the index and finish fast.
# This script submits chunks in sequence and appends results.
# Usage: bash gaia_chunked.sh <outdir> [n_chunks] [total_space]
set -uo pipefail
OUTDIR="$1"; N="${2:-256}"; TOTAL="${3:-35184372088832}"   # 2^45 ≈ full used space
TAP="https://gea.esac.esa.int/tap-server/tap"
CHUNK=$(( TOTAL / N ))
mkdir -p "$OUTDIR"
QCOLS="source_id,ra,dec,pmra,pmdec,parallax,parallax_error,phot_g_mean_mag,phot_bp_mean_mag,phot_rp_mean_mag,bp_rp,ruwe"
for i in $(seq 0 $((N-1))); do
  LO=$(( i * CHUNK )); HI=$(( (i+1) * CHUNK - 1 ))
  F="$OUTDIR/chunk_$(printf %04d $i).csv"
  [ -s "$F" ] && continue
  JOB=$(curl -sS -m 30 -X POST "$TAP/async" -D - -o /dev/null \
    --data-urlencode "REQUEST=doQuery" --data-urlencode "LANG=ADQL" \
    --data-urlencode "FORMAT=csv" --data-urlencode "PHASE=RUN" \
    --data-urlencode "QUERY=SELECT $QCOLS FROM gaiadr3.gaia_source WHERE source_id BETWEEN $LO AND $HI AND (pmra*pmra + pmdec*pmdec) > 22500 AND phot_g_mean_mag < 20 AND parallax IS NOT NULL AND ruwe < 1.4" \
    | grep -i "^location:" | tr -d '\r' | awk '{print $2}')
  [ -z "$JOB" ] && { echo "[$i] submit failed"; sleep 5; continue; }
  for t in $(seq 1 30); do
    P=$(curl -s -m 15 "$JOB/phase")
    case "$P" in
      COMPLETED) curl -s -m 30 "$JOB/results/result" -o "$F"; echo "[$i] done ($(wc -l < "$F") lines)"; break;;
      ERROR) curl -s -m 15 "$JOB/error" | grep -oE "<uws:message>[^<]*" | head -1; echo "[$i] ERROR"; break;;
      ABORTED) echo "[$i] ABORTED"; break;;
    esac
    sleep 2
  done
done
echo "chunks complete; merging..."
head -1 "$OUTDIR"/chunk_0000.csv > "$OUTDIR/all_high_pm.csv"
for f in "$OUTDIR"/chunk_*.csv; do tail -n +2 "$f"; done >> "$OUTDIR/all_high_pm.csv"
wc -l "$OUTDIR/all_high_pm.csv"
