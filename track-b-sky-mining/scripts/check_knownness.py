#!/usr/bin/env python3
"""check_knownness.py — epoch-aware same-object check for top candidates.

The v1 vetting excludes known objects by Gaia DR3 source_id only. But many
known high-PM stars are in SIMBAD under pre-Gaia designations (2MASS/LSPM/
NLTT/LHS...) without a Gaia DR3 cross-id, so source-id exclusion misses them.
A same-object match appears as a SIMBAD entry ~pm*16 yr away (2MASS epoch
2000 vs Gaia epoch 2016).

This script runs a 5-arcmin SIMBAD cone for each of the top N candidates and
classifies:
  same-object  — nearest SIMBAD sep < 1.3 * pm*16yr (or the SIMBAD name is
                 the candidate's own "Gaia DR3 <id>")
  possible-new — no such match (true discovery space; needs follow-up)

Writes results/knownness_top<N>.json and prints counts. This is the
prototype of the v2 position-based exclusion.

Usage: python3 check_knownness.py [N]   (default N=100)
"""
import csv
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_dossiers import simbad_nearest  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results")
N = int(sys.argv[1]) if len(sys.argv) > 1 else 100


def main():
    with open(os.path.join(RES, "candidates.csv")) as f:
        rows = list(csv.DictReader(f))[:N]
    path = os.path.join(RES, f"knownness_top{N}.json")
    out = {}
    same = new = fail = 0
    for i, c in enumerate(rows, 1):
        key = c["source_id"]
        pm = float(c["pm_tot"])
        tol = max(0.033, pm * 16.0 / 1000.0 / 60.0 * 1.3)
        try:
            sim = simbad_nearest(float(c["ra"]), float(c["dec"]))
        except Exception as e:
            print(f"{i:>4} {key} FAILED {e}", flush=True)
            out[key] = {"status": "failed", "error": str(e)}
            fail += 1
            continue
        hit = bool(sim and (sim[0]["name"].strip('"').endswith(key) or
                            sim[0]["sep_arcmin"] < tol))
        out[key] = {"status": "same-object" if hit else "possible-new",
                    "nearest": sim[0] if sim else None, "tol_arcmin": tol}
        same += hit
        new += not hit
        if i % 10 == 0:
            print(f"{i}/{N} done (same {same}, possible-new {new})", flush=True)
            json.dump(out, open(path, "w"), indent=1)  # checkpoint
        time.sleep(0.4)
    json.dump(out, open(path, "w"), indent=1)
    print(f"same-object (pre-Gaia known, missing cross-id): {same}")
    print(f"possible-new (survive epoch-aware check): {new}")
    print(f"failed lookups: {fail}")
    print(f"-> {path}")


if __name__ == "__main__":
    main()
