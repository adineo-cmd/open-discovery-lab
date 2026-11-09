#!/usr/bin/env python3
"""merge_chunks.py — merge the legacy aip_chunked.py output with all
aip_parallel.py part files into a single deduplicated results/chunks/all_high_pm.csv.

- Legacy file: strip NUL-padded bytes (the 2026-11-09 run had a 793 KB NUL
  prefix and no header line), drop malformed lines.
- Part files (part_<start>_<end>.csv): drop their single header line, drop
  malformed lines.
- Dedupe on source_id (first occurrence wins) — the legacy file overlaps
  chunk 1803 with worker W1's range by design.
- Sort by source_id for a canonical, comparable output.

Usage: python3 merge_chunks.py
Writes: results/chunks/all_high_pm.csv and results/chunks/merge_report.txt
"""
import csv
import glob
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
CHUNKS = os.path.join(HERE, "..", "results", "chunks")
MAIN = os.path.join(CHUNKS, "all_high_pm.csv")
HEADER = ("source_id,ra,dec,pmra,pmdec,parallax,parallax_error,"
          "phot_g_mean_mag,phot_bp_mean_mag,phot_rp_mean_mag,bp_rp,ruwe").split(",")
NUM = re.compile(r"^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$")


def valid(row):
    if len(row) != len(HEADER):
        return False
    if not re.fullmatch(r"\d{1,20}", row[0]):
        return False
    for v in row[1:]:
        if v != "" and not NUM.match(v):
            return False
    return True


def main():
    seen = {}
    report = []

    # 1. legacy single-worker file (NUL-prefixed, headerless)
    legacy_rows = legacy_bad = 0
    if os.path.exists(MAIN):
        with open(MAIN, "rb") as f:
            raw = f.read().replace(b"\x00", b"")
        for line in raw.split(b"\n"):
            line = line.decode("utf-8", "replace").strip()
            if not line or line.startswith("source_id"):
                continue
            row = line.split(",")
            if valid(row):
                seen[row[0]] = line
                legacy_rows += 1
            else:
                legacy_bad += 1
        report.append(f"legacy all_high_pm.csv: {legacy_rows} rows kept, "
                      f"{legacy_bad} malformed dropped")
    else:
        report.append("legacy all_high_pm.csv: not found (skipped)")

    # 2. part files
    for part in sorted(glob.glob(os.path.join(CHUNKS, "part_*.csv"))):
        rows = part_bad = part_dup = 0
        with open(part, errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("source_id"):
                    continue
                row = line.split(",")
                if not valid(row):
                    part_bad += 1
                    continue
                if row[0] in seen:
                    part_dup += 1
                    continue
                seen[row[0]] = line
                rows += 1
        report.append(f"{os.path.basename(part)}: {rows} new rows, {part_dup} "
                      f"duplicates skipped, {part_bad} malformed dropped")

    # 3. write canonical merged file (sorted by source_id)
    out_rows = sorted(seen.values(), key=lambda l: int(l.split(",")[0]))
    with open(MAIN, "w") as f:
        f.write(",".join(HEADER) + "\n")
        f.write("\n".join(out_rows) + "\n")

    report.append(f"MERGED total: {len(out_rows)} rows -> "
                  f"{os.path.relpath(MAIN, HERE)} (header restored, sorted by source_id)")
    with open(os.path.join(CHUNKS, "merge_report.txt"), "w") as f:
        f.write("\n".join(report) + "\n")
    print("\n".join(report))


if __name__ == "__main__":
    main()
