#!/usr/bin/env python3
"""aip_chunked.py — chunked high-PM harvest from Gaia DR3 via gaia.aip.de sync TAP.

ESAC's anonymous tier caps async jobs at 60 s (full-sky scans abort); the AIP
mirror answers a 2^37-id chunk scan in ~2 s. We walk source_id space in chunks
(PK range → index scan) and merge everything.

Usage: python3 aip_chunked.py <outdir> [n_chunks]
"""
import os
import re
import sys
import time
import urllib.parse
import urllib.request

OUT = sys.argv[1] if len(sys.argv) > 1 else "chunks"
N = int(sys.argv[2]) if len(sys.argv) > 2 else 4096
# Empirical Gaia DR3 source_id range (probed via MIN/MAX on gaia.aip.de):
# min 4.3e9, max 6.92e18. Ids cluster in level bands; empty chunks are cheap.
LO_ALL = 0
HI_ALL = 7 * (1 << 60)  # 6.92e18 max observed, padded
BASE = LO_ALL
TOTAL = HI_ALL
CHUNK = (TOTAL - BASE) // N
TAP = "https://gaia.aip.de/tap/sync"
COLS = ("source_id,ra,dec,pmra,pmdec,parallax,parallax_error,"
        "phot_g_mean_mag,phot_bp_mean_mag,phot_rp_mean_mag,bp_rp,ruwe")
QUERY = ("SELECT {cols} FROM gaiadr3.gaia_source WHERE source_id BETWEEN {lo} AND {hi} "
         "AND (pmra*pmra + pmdec*pmdec) > 22500 AND phot_g_mean_mag < 20 "
         "AND parallax IS NOT NULL AND ruwe < 1.4")

TD = re.compile(r"<TD[^>]*>([^<]*)</TD>", re.I)


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
        header = None
        for tr in re.findall(r"<TR>(.*?)</TR>", body, re.S | re.I):
            vals = [v.strip() for v in TD.findall(tr)]
            if vals:
                rows.append(vals)
        m = re.findall(r'<FIELD[^>]*name="([^"]+)"', body)
        if m:
            header = m
        return header, rows
    lines = [l for l in body.splitlines() if l.strip()]
    return lines[0].split(","), [l.split(",") for l in lines[1:]]


def main():
    os.makedirs(OUT, exist_ok=True)
    out_csv = os.path.join(OUT, "all_high_pm.csv")
    merged_header = None
    total_rows = 0
    mode = "a" if os.path.exists(out_csv) else "w"
    with open(out_csv, mode) as out:
        for i in range(N):
            lo, hi = i * CHUNK, (i + 1) * CHUNK - 1
            try:
                body = fetch(lo, hi)
                header, rows = parse(body)
                if rows:
                    if merged_header is None:
                        merged_header = header or rows[0]
                        out.write(",".join(map(str, merged_header)) + "\n")
                    for r in rows:
                        out.write(",".join(r) + "\n")
                    total_rows += len(rows)
                print(f"chunk {i:04d}: {len(rows)} rows", flush=True)
            except Exception as e:
                print(f"chunk {i:04d}: FAIL {e}", flush=True)
                time.sleep(3)
    print(f"TOTAL rows: {total_rows} → {out_csv}", flush=True)


if __name__ == "__main__":
    main()
