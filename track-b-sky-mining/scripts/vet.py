#!/usr/bin/env python3
"""vet.py — reduce the high-PM harvest to a vetted candidate list.

Steps:
 1. Load results/chunks/all_high_pm.csv (from aip_chunked.py).
 2. Load known-object source_id sets (GCNS J/A+A/649/A6 + Kirkpatrick
    J/ApJS/253/7 + J/ApJS/271/55 via VizieR TSV — see download_known.sh).
 3. Rank survivors by reduced proper motion (H = G + 5*log10(pm) — high H
    with faint G and red colour ⇒ ultracool-dwarf-like).
 4. Emit results/candidates.csv (candidates only; exclusions counted,
    reasons logged).

Usage: python3 vet.py
"""
import csv
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results")
KNOWN_FILES = [
    os.path.join(RES, "known", "gcns_sources.txt"),
    os.path.join(RES, "known", "kirkpatrick2021_sources.txt"),
    os.path.join(RES, "known", "kirkpatrick2024_sources.txt"),
]


def load_known():
    known = set()
    for f in KNOWN_FILES:
        if not os.path.exists(f):
            print(f"WARN missing known file: {f}", file=sys.stderr)
            continue
        with open(f) as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#"):
                    known.add(line)
    return known


def rpm(g, pm):
    """Reduced proper motion H = G + 5*log10(pm[mas/yr]/1000)."""
    if pm <= 0 or g is None:
        return None
    return g + 5.0 * math.log10(pm / 1000.0)


def main():
    src = os.path.join(RES, "chunks", "all_high_pm.csv")
    if not os.path.exists(src):
        sys.exit("harvest not found: run aip_chunked.py first")
    known = load_known()
    total = excluded = flagged = 0
    cands = []
    with open(src) as f:
        rd = csv.DictReader(f)
        for row in rd:
            total += 1
            sid = row["source_id"].strip()
            if sid in known:
                excluded += 1
                continue
            try:
                pmra, pmdec = float(row["pmra"]), float(row["pmdec"])
                g = float(row["phot_g_mean_mag"])
                plx = float(row["parallax"])
                bprp = float(row["bp_rp"]) if row.get("bp_rp") not in ("", None) else None
            except (ValueError, KeyError):
                continue
            pm_tot = math.hypot(pmra, pmdec)
            h = rpm(g, pm_tot)
            # ultracool-dwarf-like: red, faint, slow-luminosity fast-moving
            if bprp is not None and bprp > 2.5 and h is not None and h > 16.0:
                flagged += 1
                cands.append({
                    "source_id": sid, "ra": row["ra"], "dec": row["dec"],
                    "pmra": pmra, "pmdec": pmdec, "pm_tot": round(pm_tot, 1),
                    "parallax": plx, "dist_pc": round(1000.0 / plx, 1) if plx > 0 else "",
                    "G": g, "bp_rp": bprp, "H_rpm": round(h, 2),
                    "d_flags": row.get("dup", ""),
                })
    cands.sort(key=lambda c: -c["H_rpm"])
    out = os.path.join(RES, "candidates.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(cands[0].keys()) if cands else ["source_id"])
        w.writeheader()
        w.writerows(cands)
    print(f"harvest rows: {total} · excluded (known): {excluded} · "
          f"ultracool-like candidates: {flagged} → {out}")


if __name__ == "__main__":
    main()
