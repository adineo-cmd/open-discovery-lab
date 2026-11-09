#!/bin/bash
# gaia_query.sh — submit async ADQL job to Gaia DR3 TAP and poll to completion.
# Usage: bash gaia_query.sh <query.adql-file> <output.csv>
# Reproducibility: query text is version-controlled; job IDs logged to journal.
set -euo pipefail
QFILE="$1"; OUT="$2"
TAP="https://gea.esac.esa.int/tap-server/tap"
JOB=$(curl -s -X POST "$TAP/async" \
  --data-urlencode "REQUEST=doQuery" \
  --data-urlencode "LANG=ADQL" \
  --data-urlencode "FORMAT=csv" \
  --data-urlencode "PHASE=RUN" \
  --data-urlencode "QUERY=$(cat "$QFILE")" \
  -D - -o /dev/null | grep -i "^location:" | tr -d '\r' | awk '{print $2}')
echo "job: $JOB"
for i in $(seq 1 60); do
  PHASE=$(curl -s "$JOB/phase")
  echo "[$i] phase: $PHASE"
  case "$PHASE" in
    COMPLETED) curl -s "$JOB/results/result" -o "$OUT"; echo "saved: $OUT ($(wc -l < "$OUT") lines)"; exit 0;;
    ERROR) curl -s "$JOB/error" >&2; exit 1;;
    ABORTED) echo "job aborted" >&2; exit 1;;
  esac
  sleep 20
done
echo "timeout waiting for $JOB" >&2; exit 1
