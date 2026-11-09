#!/usr/bin/env python3
"""vet.py — reduce the high-PM harvest to a vetted candidate list.

Steps:
 1. Load results/chunks/all_high_pm.csv (harvest: aip_chunked.py +
    aip_parallel.py part files merged by merge_chunks.py).
 2. Load known-object source_id sets from results/known/*.txt
    (dynamic glob; sets written by build_known.py / download_known.sh:
    GCNS I/364/gcns, Kirkpatrick 2024 20-pc census, Simbad UCD otypes).
 3. Rank survivors by reduced proper motion (H = G + 5*log10(pm) — high H
    with faint G and red colour ⇒ ultracool-dwarf-like).
 4. Emit results/candidates.csv (candidates only; exclusions counted).

Usage: python3 vet.py
"""
import csv
import glob
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results")
csv.field_size_limit(1 << 24)  # tolerate junk/padded rows (e.g. NUL prefixes)


def known_files():
    """Every results/known/*.txt is an exclusion set (build_known.py writes
    them with a '# ' header; one source_id per line)."""
    return sorted(glob.glob(os.path.join(RES, "known", "*.txt")))


def load_known():
    known = set()
    for f in known_files():
        if not os.path.exists(f):
            print(f"WARN missing known file: {f}", file=sys.stderr)
            continue
        n = 0
        with open(f) as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#"):
                    known.add(line)
                    n += 1
        print(f"known: {os.path.basename(f)} -> {n} ids")
    return known


def rpm(g, pm):
    """Reduced proper motion H = G + 5*log10(pm[mas/yr]/1000)."""
    if pm <= 0 or g is None:
        return None
    return g + 5.0 * math.log10(pm / 1000.0)


def main():
    src = os.path.join(RES, "chunks", "all_high_pm.csv")
    if not os.path.exists(src):
        sys.exit("harvest not found: run aip_chunked.py / aip_parallel.py first")
    known = load_known()
    header = ("source_id,ra,dec,pmra,pmdec,parallax,parallax_error,"
              "phot_g_mean_mag,phot_bp_mean_mag,phot_rp_mean_mag,bp_rp,ruwe").split(",")
    idx = {name: i for i, name in enumerate(header)}
    total = excluded = bad = flagged = 0
    cands = []
    with open(src, errors="replace") as f:
        rd = csv.reader(f)
        first = next(rd, None)
        rows = [first] + list(rd) if first is not None else []
        for row in rows:
            # tolerate a headerless file or a stray padded line
            if len(row) != len(header) or not row[0].strip().isdigit():
                bad += 1
                continue
            total += 1
            sid = row[idx["source_id"]].strip()
            if sid in known:
                excluded += 1
                continue
            try:
                pmra, pmdec = float(row[idx["pmra"]]), float(row[idx["pmdec"]])
                g = float(row[idx["phot_g_mean_mag"]])
                plx = float(row[idx["parallax"]])
                bprp = row[idx["bp_rp"]]
                bprp = float(bprp) if bprp not in ("", None) else None
            except (ValueError, KeyError, IndexError):
                bad += 1
                continue
            pm_tot = math.hypot(pmra, pmdec)
            h = rpm(g, pm_tot)
            # ultracool-dwarf-like: red, faint, slow-luminosity fast-moving
            if bprp is not None and bprp > 2.5 and h is not None and h > 16.0:
                flagged += 1
                cands.append({
                    "source_id": sid, "ra": row[idx["ra"]], "dec": row[idx["dec"]],
                    "pmra": pmra, "pmdec": pmdec, "pm_tot": round(pm_tot, 1),
                    "parallax": plx, "dist_pc": round(1000.0 / plx, 1) if plx > 0 else "",
                    "G": g, "bp_rp": bprp, "H_rpm": round(h, 2),
                    "ruwe": row[idx["ruwe"]],
                })
    cands.sort(key=lambda c: -c["H_rpm"])
    out = os.path.join(RES, "candidates.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(cands[0].keys()) if cands else ["source_id"])
        w.writeheader()
        w.writerows(cands)
    print(f"harvest rows: {total} · excluded (known): {excluded} · "
          f"malformed skipped: {bad} · ultracool-like candidates: {flagged} → {out}")


if __name__ == "__main__":
    main()
