#!/usr/bin/env python3
"""aip_parallel.py — parallel high-PM harvest worker for Gaia DR3 via gaia.aip.de.

Same chunked query as aip_chunked.py, but this worker takes an EXPLICIT chunk
range [start, end) and appends its rows to its OWN part file
results/chunks/part_<start>_<end>.csv. No shared output file, no cross-worker
collisions; dedupe happens at merge time (scripts/merge_chunks.py).

Chunk layout must match aip_chunked.py: with N=4096 chunks over source_id
range [0, 7*2^60), chunk i covers source_id [i*7*2^48, (i+1)*7*2^48 - 1].

Usage: python3 aip_parallel.py <outdir> <start_chunk> <end_chunk>
       (end_chunk exclusive; e.g. 1803 2261 covers chunks 1803..2260)
"""
import os
import re
import sys
import time
import urllib.parse
import urllib.request

OUT = sys.argv[1] if len(sys.argv) > 1 else "chunks"
START = int(sys.argv[2]) if len(sys.argv) > 2 else 0
END = int(sys.argv[3]) if len(sys.argv) > 3 else 4096
N_TOTAL = 4096
LO_ALL = 0
HI_ALL = 7 * (1 << 60)
CHUNK = HI_ALL // N_TOTAL  # = 7 * 2^48, matches aip_chunked.py
TAP = "https://gaia.aip.de/tap/sync"
COLS = ("source_id,ra,dec,pmra,pmdec,parallax,parallax_error,"
        "phot_g_mean_mag,phot_bp_mean_mag,phot_rp_mean_mag,bp_rp,ruwe")
QUERY = ("SELECT {cols} FROM gaiadr3.gaia_source WHERE source_id BETWEEN {lo} AND {hi} "
         "AND (pmra*pmra + pmdec*pmdec) > 22500 AND phot_g_mean_mag < 20 "
         "AND parallax IS NOT NULL AND ruwe < 1.4")
HEADER = COLS.split(",")

TD = re.compile(r"<TD[^>]*>([^<]*)</TD>", re.I)
MAX_TRIES = 4


def fetch(lo, hi):
    q = QUERY.format(cols=COLS, lo=lo, hi=hi)
    data = urllib.parse.urlencode({
        "REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "csv", "QUERY": q
    }).encode()
    req = urllib.request.Request(TAP, data=data, headers={"User-Agent": "open-discovery-lab/0.1"})
    with urllib.request.urlopen(req, timeout=120) as r:
        body = r.read().decode("utf-8", "replace")
    return body


def parse(body):
    """Return (header, rows) from CSV or VOTABLE body."""
    if body.lstrip().startswith("<?xml") or "<VOTABLE" in body[:200]:
        rows = []
        for tr in re.findall(r"<TR>(.*?)</TR>", body, re.S | re.I):
            vals = [v.strip() for v in TD.findall(tr)]
            if vals:
                rows.append(vals)
        header = re.findall(r'<FIELD[^>]*name="([^"]+)"', body) or None
        return header, rows
    lines = [l for l in body.splitlines() if l.strip()]
    if not lines:
        return HEADER, []
    if lines[0].lstrip().startswith("source_id"):
        lines = lines[1:]
    return HEADER, [l.split(",") for l in lines]


def main():
    os.makedirs(OUT, exist_ok=True)
    part = os.path.join(OUT, f"part_{START}_{END}.csv")
    total_rows = 0
    failed = []
    with open(part, "w") as out:
        out.write(",".join(HEADER) + "\n")
        for i in range(START, END):
            lo, hi = i * CHUNK, (i + 1) * CHUNK - 1
            rows = None
            for attempt in range(MAX_TRIES):
                try:
                    body = fetch(lo, hi)
                    header, rows = parse(body)
                    break
                except Exception as e:
                    print(f"chunk {i:04d} try{attempt + 1}: FAIL {e}", flush=True)
                    time.sleep(5 * (attempt + 1))
                    rows = None
            if rows is None:
                failed.append(i)
                continue
            for r in rows:
                out.write(",".join(r) + "\n")
            total_rows += len(rows)
            print(f"chunk {i:04d}: {len(rows)} rows (worker total {total_rows})", flush=True)
    print(f"WORKER [{START},{END}) done: {total_rows} rows, {len(failed)} failed chunks "
          f"{failed[:20]} -> {part}", flush=True)


if __name__ == "__main__":
    main()
