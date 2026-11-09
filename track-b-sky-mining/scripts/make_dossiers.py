#!/usr/bin/env python3
"""make_dossiers.py — build results/candidates_top20.md from results/candidates.csv.

For each of the top 20 candidates (highest reduced proper motion H):
  - legacy-survey DR9 cutout URL (not downloaded, link only)
  - nearest known object checks: Simbad CFA TAP cone (5 arcmin, top 3 with
    otypes) and GCNS via G-VO TAP cone (5 arcmin, nearest source_id)
  - one-line why-interesting (dist < 100 pc + red + high RPM =>
    ultracool-dwarf-like; here most candidates sit just beyond the GCNS
    100 pc wall with L/T-dwarf colours and H)

Cone results are cached in results/known_checks.json (successful lookups
only; failures are retried and NOT cached).

Usage: python3 make_dossiers.py [N]
"""
import csv
import json
import os
import sys
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results")
CACHE = os.path.join(RES, "known_checks.json")
N_TOP = int(sys.argv[1]) if len(sys.argv) > 1 else 20
CONE_DEG = 5.0 / 60.0  # 5 arcmin


def tap(url_base, query, timeout=90):
    q = urllib.parse.urlencode({
        "REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "csv", "QUERY": query
    })
    req = urllib.request.Request(f"{url_base}?{q}",
                                 headers={"User-Agent": "open-discovery-lab/0.1"})
    last_err = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:
            last_err = e
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"TAP failed after retries: {last_err}")


def cone_query(ra, dec, cols, table):
    return (f"SELECT TOP 3 {cols}, DISTANCE(POINT('ICRS', ra, dec), "
            f"POINT('ICRS', {ra!r}, {dec!r})) AS sep "
            f"FROM {table} WHERE 1=CONTAINS(POINT('ICRS', ra, dec), "
            f"CIRCLE('ICRS', {ra!r}, {dec!r}, {CONE_DEG})) ORDER BY sep ASC")


def simbad_nearest(ra, dec):
    body = tap("https://simbad.cfa.harvard.edu/simbad/sim-tap/sync",
               cone_query(ra, dec, "main_id, otype, ra, dec", "basic"))
    out = []
    for row in csv.reader(body.splitlines()[1:]):
        if row and len(row) >= 5:
            out.append({"name": row[0].strip('"'), "otype": row[1].strip('"'),
                        "sep_arcmin": round(float(row[4]) * 60.0, 2)})
    return out


def gcns_nearest(ra, dec):
    body = tap("https://dc.g-vo.org/tap/sync",
               cone_query(ra, dec, "source_id, ra, dec", "gcns.main"))
    out = []
    for row in csv.reader(body.splitlines()[1:]):
        if row and len(row) >= 4:
            out.append({"source_id": row[0].strip('"'),
                        "sep_arcmin": round(float(row[3]) * 60.0, 2)})
    return out


def main():
    src = os.path.join(RES, "candidates.csv")
    with open(src) as f:
        rows = list(csv.DictReader(f))[:N_TOP]
    cache = {}
    if os.path.exists(CACHE):
        cache = json.load(open(CACHE))

    head = ["# Track B — top 20 candidates (highest reduced proper motion)", "",
            "Harvest: full-sky Gaia DR3 high-PM scan (|pm|>150 mas/yr, G<20, RUWE<1.4,",
            "parallax measured) via gaia.aip.de sync TAP in 4096 source_id chunks",
            "(scripts/aip_chunked.py + aip_parallel.py, merged by merge_chunks.py).",
            "Exclusions: GCNS (I/364/gcns), Kirkpatrick+2024 20-pc census, SIMBAD",
            "LM*/BD*/SD*/WD* otypes (results/known/). Vetting: bp_rp>2.5,",
            "H=G+5*log10(pm)>16 — ultracool-dwarf-like.", "",
            "Nearest-known cones: 5 arcmin around each candidate (SIMBAD basic and",
            "GCNS gcns.main, both via TAP). Cutouts: Legacy Survey DR9 jpeg 200px.",
            "", "Rank | source_id | ra,dec | pm_tot | dist(pc) | G | bp_rp | H |",
            "---|---|---|---|---|---|---|---|"]
    sections = []
    for i, c in enumerate(rows, 1):
        key = c["source_id"]
        ra, dec = float(c["ra"]), float(c["dec"])
        if key not in cache:
            sim = gc = None
            for attempt in range(3):
                try:
                    sim = simbad_nearest(ra, dec)
                    gc = gcns_nearest(ra, dec)
                    break
                except Exception as e:
                    print(f"{key} cone attempt {attempt + 1} failed: {e}")
                    time.sleep(10)
            if sim is None or gc is None:
                raise RuntimeError(f"cone lookups kept failing for {key}")
            cache[key] = {"simbad": sim, "gcns": gc}
            json.dump(cache, open(CACHE, "w"), indent=1)
            time.sleep(1)
        info = cache[key]
        sim = info.get("simbad", [])
        gc = info.get("gcns", [])
        pm = float(c["pm_tot"])
        # 2MASS/ULAS designations are epoch-2000 positions; Gaia epoch is
        # 2016.0, so a same-object match sits ~pm*16yr away on the sky.
        same_tol_arcmin = max(0.033, pm * 16.0 / 1000.0 / 60.0 * 1.3)
        same_obj = sim and (
            sim[0]["name"].strip('"').endswith(key) or
            sim[0]["sep_arcmin"] < same_tol_arcmin)
        sim_s = (f"nearest SIMBAD: {sim[0]['name']} ({sim[0]['otype']}) at "
                 f"{sim[0]['sep_arcmin']} arcmin") if sim else \
            "no SIMBAD object within 5 arcmin"
        gc_s = (f"nearest GCNS: {gc[0]['source_id']} at "
                f"{gc[0]['sep_arcmin']} arcmin") if gc else \
            "no GCNS source within 5 arcmin"
        flag = ""
        if same_obj:
            flag = (f" — LIKELY SAME OBJECT (separation matches the "
                    f"~{pm * 16.0 / 1000.0:.1f} arcsec epoch-2000→2016 proper-motion "
                    f"offset; Simbad lacks the Gaia DR3 cross-id, so source-id "
                    f"exclusion missed it)")
        cutout = (f"https://www.legacysurvey.org/viewer/jpeg-cutout?ra={ra}&dec={dec}"
                  f"&layer=ls-dr9&size=200")
        head.append(f"{i} | [{key}](#{i}-gaia-dr3-{key}) | {ra:.5f}, {dec:.5f} | "
                    f"{c['pm_tot']} | {c['dist_pc']} | {float(c['G']):.2f} | "
                    f"{float(c['bp_rp']):.2f} | {c['H_rpm']} |")
        sections.append(f"### {i}. Gaia DR3 {key}")
        sections.append(f"- position: {ra:.6f} {dec:.6f}  ·  "
                        f"pm_tot {c['pm_tot']} mas/yr  ·  dist {c['dist_pc']} pc  ·  "
                        f"G {float(c['G']):.2f}  ·  bp_rp {float(c['bp_rp']):.2f}  ·  "
                        f"H {c['H_rpm']}  ·  RUWE {float(c['ruwe']):.3f}")
        sections.append(f"- cutout: <{cutout}>")
        sections.append(f"- nearest known: {sim_s}{flag}; {gc_s}")
        verdict = ("pre-Gaia-designation object missing its Gaia DR3 cross-id in "
                   "SIMBAD — recovery, not discovery" if same_obj else
                   "red (bp_rp "
                   f"{float(c['bp_rp']):.2f} > 2.5), faint (G {float(c['G']):.2f}), "
                   f"fast ({c['pm_tot']} mas/yr) with H {c['H_rpm']} > 16 at "
                   f"{c['dist_pc']} pc — just beyond the GCNS 100 pc wall and absent "
                   "from all exclusion sets (ultracool-dwarf-like; follow-up "
                   "recommended)")
        sections.append(f"- verdict: {verdict}")
        sections.append("")
    out = os.path.join(RES, "candidates_top20.md")
    with open(out, "w") as f:
        f.write("\n".join(head) + "\n\n" + "\n".join(sections))
    print(f"wrote {out} ({len(rows)} dossiers)")


if __name__ == "__main__":
    main()
