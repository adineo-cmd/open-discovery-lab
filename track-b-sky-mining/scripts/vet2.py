#!/usr/bin/env python3
"""vet2.py — epoch-aware vetting v2 for ALL ultracool-dwarf-like candidates.

Motivation (finding F-11): source-id exclusion is insufficient — pre-Gaia
recoveries live in SIMBAD under 2MASS/LSPM/NLTT/LHS names without Gaia DR3
cross-ids. A same-object match appears as a SIMBAD entry displaced along the
proper-motion vector by pm x |epoch_SIMBAD - 2016.0|.

Epoch model (explicit per catalog):
  Gaia DR3 astrometry        : epoch 2016.0  (our candidate positions)
  SIMBAD basic.ra/dec        : stored at catalog measurement epoch; for the
    vast majority of entries that is J2000-ish. A hit measured at epoch t has
    sep(hit, pos2016) ~ pm*|2016-t|. Our match rules:
      tol2000  : sep(hit, pos propagated BACK to 2000.0) < 1.3*pm*16yr
                 -> covers stored epochs 1979.2..2016.0
      tolNow   : sep(hit, pos propagated FWD to EPOCH_NOW) < 1.3*pm*10.86yr
                 -> covers stored epochs 2012.7..EPOCH_NOW (modern entries)
      corr-old : PM-track projection for hits with implied epoch 1950..1979.2
                 (old LHS/NLTT-era entries); requires perpendicular residual
                 perp <= max(2", 0.12*pm*16yr) AND implied epoch in range.
                 Weaker rule (a ~4 arcsec-wide corridor over ~5 arcmin);
                 matches are flagged and downgraded in confidence.
  CatWISE2020 (IRSA)         : ra/dec at epoch 2015.5; pm in deg/yr (IRSA).
  GCNS (gcns.main)           : Gaia EDR3 epoch 2016.0, EDR3 source ids.

Screens (per candidate):
  1. harvest self-match  : any OTHER harvest row within 2" at epoch 2016.0
                           -> DUPLICATE (Gaia double detection / close pair)
  2. GCNS by source_id   : local results/known/*.txt id sets (GCNS entries
                           carry EDR3 ids, so id exclusion is sufficient there)
  3. SIMBAD 5' cone around the pre-Gaia (epoch-2000) position, TOP 12 hits,
     all hits evaluated with the rules above (phase `sweep`)
  4. survivors: SIMBAD 5' cone around the present-day position (phase
     `survivors`; geometrically ~redundant — the whole 1979..2027 PM track
     spans <= 21" for |pm|<=1500 mas/yr, well inside one 5' cone — but kept
     as an explicit re-check), SIMBAD ident lookup for 'Gaia DR3 <id>' and
     'Gaia EDR3 <id>', IRSA CatWISE2020 cone at the epoch-2015.5 position,
     G-VO GCNS 5' cone at the 2016.0 position (shortlist only)

Classification: K known / P possible-new / D duplicate / F failed lookup.
Confidence (possible-new only): A / B / C — see finalize().

Every HTTP query is appended to results/vetting_v2_querylog.csv ( flushed
incrementally; per-process counter keeps repeats out on resume). State is
checkpointed to results/vetting_v2_state.json every 25 candidates;
re-running a phase resumes from the checkpoint. Committing: the git
artifacts are the compact renders from scripts/render_git_csvs.py (run
scripts/apply_lit_checks.py first to fold in imagery/literature columns).

Usage: python3 vet2.py sweep|survivors|finalize|all
"""
import csv
import json
import math
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results")
CANDS = os.path.join(RES, "candidates.csv")
HARVEST = os.path.join(RES, "chunks", "all_high_pm.csv")
STATE = os.path.join(RES, "vetting_v2_state.json")
QLOG = os.path.join(RES, "vetting_v2_querylog.csv")

EPOCH_GAIA = 2016.0          # Gaia DR3 reference epoch
EPOCH_CAT = 2000.0           # typical pre-Gaia catalog epoch (2MASS/LSPM/NLTT)
EPOCH_NOW = 2026.859         # this session (UTC 2026-11-10 15:15)
EPOCH_WISE = 2015.5          # CatWISE2020 reference epoch
CONE_DEG = 5.0 / 60.0        # 5 arcmin
DUP_TOL_AS = 2.0             # harvest self-match radius at epoch 2016.0
TOL_K = 1.3                  # tolerance factor (same as check_knownness.py v1)
SIMBAD_URL = "https://simbad.cfa.harvard.edu/simbad/sim-tap/sync"
GVO_URL = "https://dc.g-vo.org/tap/sync"
IRSA_URL = "https://irsa.ipac.caltech.edu/TAP/sync"
N_THREADS = 2                # ~1.5 req/s across two hosts max; polite
N_TOP_HITS = 12


def tap(url_base, query, timeout=120, attempts=3):
    q = urllib.parse.urlencode({
        "REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "csv", "QUERY": query
    })
    req = urllib.request.Request(f"{url_base}?{q}",
                                 headers={"User-Agent": "open-discovery-lab/0.2"})
    last_err, t0 = None, time.time()
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = r.read().decode("utf-8", "replace")
                return body, time.time() - t0
        except Exception as e:
            last_err = e
            time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"TAP failed after {attempts} attempts: {last_err}")


def parse_csv(body):
    """Rows as lists; tolerate VOTABLE error responses (returned as XML)."""
    lines = [l for l in body.splitlines() if l.strip()]
    if not lines or lines[0].lstrip().startswith("<?xml"):
        raise ValueError("TAP returned XML (error?)")
    return list(csv.reader(lines))


def propagate(ra, dec, pmra, pmdec, dt):
    """Gaia position propagated by dt years (mas/yr -> deg, pmra already
    includes the cos(dec) factor)."""
    dec_r = math.radians(dec)
    ra2 = ra + (pmra * dt / 3.6e6) / max(math.cos(dec_r), 0.02)
    dec2 = dec + pmdec * dt / 3.6e6
    return ((ra2 + 360.0) % 360.0, max(-90.0, min(90.0, dec2)))


def ang_sep_as(ra1, dec1, ra2, dec2):
    """Angular separation in arcsec (haversine)."""
    r1, d1, r2, d2 = map(math.radians, (ra1, dec1, ra2, dec2))
    sd = math.sin((d2 - d1) / 2.0)
    sr = math.sin((r2 - r1) / 2.0)
    a = sd * sd + math.cos(d1) * math.cos(d2) * sr * sr
    return math.degrees(2.0 * math.asin(min(1.0, math.sqrt(a)))) * 3600.0


def cone_query(ra, dec, cols, table, radius_deg=CONE_DEG, top=N_TOP_HITS):
    return (f"SELECT TOP {top} {cols}, DISTANCE(POINT('ICRS', ra, dec), "
            f"POINT('ICRS', {ra!r}, {dec!r})) AS sep FROM {table} "
            f"WHERE 1=CONTAINS(POINT('ICRS', ra, dec), "
            f"CIRCLE('ICRS', {ra!r}, {dec!r}, {radius_deg})) ORDER BY sep ASC")


def simbad_cone(ra, dec, tag, sid):
    body, dt = tap(SIMBAD_URL, cone_query(ra, dec, "main_id, otype, ra, dec", "basic"))
    hits = []
    for row in parse_csv(body)[1:]:
        if len(row) >= 5:
            hits.append({"name": row[0].strip('"'), "otype": row[1].strip('"'),
                         "ra": float(row[2]), "dec": float(row[3]),
                         "sep_as": round(float(row[4]) * 3600.0, 2)})
    return hits, dt


def gvo_cone(ra, dec, sid):
    body, dt = tap(GVO_URL, cone_query(ra, dec, "source_id, ra, dec", "gcns.main", top=5))
    hits = []
    for row in parse_csv(body)[1:]:
        if len(row) >= 4:
            hits.append({"source_id": row[0].strip('"'), "ra": float(row[1]),
                         "dec": float(row[2]), "sep_as": round(float(row[3]) * 3600.0, 2)})
    return hits, dt


def irsa_cone(ra, dec, radius_deg, sid):
    cols = ("source_id, ra, dec, pmra, pmdec, sigpmra, sigpmdec, w1mpro, w2mpro")
    body, dt = tap(IRSA_URL, cone_query(ra, dec, cols, "catwise_2020",
                                        radius_deg=radius_deg, top=8))
    hits = []
    for row in parse_csv(body)[1:]:
        if len(row) < 9:
            continue
        h = {"cw_id": row[0].strip('"'), "ra": float(row[1]), "dec": float(row[2])}
        try:
            for k, v in zip(("pmra", "pmdec", "sigpmra", "sigpmdec",
                             "w1mpro", "w2mpro"), row[3:9]):
                h[k] = None if v.strip() == "" else float(v)
        except ValueError:
            pass
        h["sep_as"] = round(ang_sep_as(ra, dec, h["ra"], h["dec"]), 2)
        hits.append(h)
    hits.sort(key=lambda h: h["sep_as"])
    return hits, dt


def load_candidates():
    with open(CANDS) as f:
        rows = list(csv.DictReader(f))
    return rows


def load_harvest_grid():
    """Harvest rows indexed on a 0.02-deg grid for 2-arcsec self-matching."""
    grid = {}
    meta = {}
    with open(HARVEST, errors="replace") as f:
        rd = csv.DictReader(f)
        for row in rd:
            try:
                ra, dec = float(row["ra"]), float(row["dec"])
                sid = row["source_id"].strip()
                meta[sid] = (float(row["parallax_error"]), row.get("parallax", ""))
            except (ValueError, KeyError):
                continue
            grid.setdefault((int(ra / 0.02), int(dec / 0.02)), []).append(
                (sid, ra, dec))
    return grid, meta


def harvest_neighbors(grid, ra, dec, tol_as=DUP_TOL_AS):
    out = []
    bx, by = int(ra / 0.02), int(dec / 0.02)
    for ix in (bx - 1, bx, bx + 1):
        for iy in (by - 1, by, by + 1):
            for sid, hra, hdec in grid.get((ix, iy), ()):
                if ang_sep_as(ra, dec, hra, hdec) <= tol_as:
                    out.append(sid)
    return out


def evaluate_hits(hits, cand, pm):
    """Apply the epoch-aware match rules to all SIMBAD hits; also return the
    minimum non-matching margin (sep/tol2000) for confidence scoring."""
    ra, dec = float(cand["ra"]), float(cand["dec"])
    ra2000, dec2000 = propagate(ra, dec, float(cand["pmra"]), float(cand["pmdec"]),
                                EPOCH_CAT - EPOCH_GAIA)
    ranow, decnow = propagate(ra, dec, float(cand["pmra"]), float(cand["pmdec"]),
                              EPOCH_NOW - EPOCH_GAIA)
    tol2000 = max(2.0, TOL_K * pm * (EPOCH_GAIA - EPOCH_CAT) / 1000.0)
    tolnow = max(2.0, TOL_K * pm * (EPOCH_NOW - EPOCH_GAIA) / 1000.0)
    drift16 = pm * (EPOCH_GAIA - EPOCH_CAT) / 1000.0  # arcsec, 2000->2016
    perp_tol = max(2.0, 0.12 * drift16)
    cosd = math.cos(math.radians(dec))
    ux, uy = float(cand["pmra"]) / pm, float(cand["pmdec"]) / pm
    best, margin = None, None
    for h in hits:
        sep2000 = ang_sep_as(ra2000, dec2000, h["ra"], h["dec"])
        sepnow = ang_sep_as(ranow, decnow, h["ra"], h["dec"])
        sepcand = ang_sep_as(ra, dec, h["ra"], h["dec"])
        m = None
        if h["name"].endswith(cand["source_id"]):
            m = ("direct-name", sepcand, None)
        elif sep2000 < tol2000:
            m = ("tol2000", sep2000, None)
        elif sepnow < tolnow:
            m = ("tolNow", sepnow, None)
        else:
            dra = (h["ra"] - ra) * cosd * 3600.0
            ddec = (h["dec"] - dec) * 3600.0
            along = dra * ux + ddec * uy
            perp = abs(dra * uy - ddec * ux)
            t_impl = EPOCH_GAIA + (along / pm if pm > 0 else 0.0)
            # tol2000 covers stored epochs > EPOCH_CAT - TOL_K*16 = 1979.2;
            # the corridor rule only needs the older window.
            if perp <= perp_tol and 1950.0 <= t_impl < (EPOCH_CAT - TOL_K * 16):
                m = ("corr-old", sepcand, round(t_impl, 1))
        if m:
            info = dict(h)
            info.update({"rule": m[0], "match_sep_as": round(m[1], 2),
                         "t_implied": m[2]})
            if best is None or info["match_sep_as"] < best["match_sep_as"]:
                best = info
        else:
            mm = min(sep2000 / tol2000, sepnow / tolnow)
            margin = mm if margin is None else min(margin, mm)
    return best, margin


def match_and_classify(cand, hits, pm, dup_sids, known_ids):
    sid = cand["source_id"]
    rec = {"status": None, "dup_neighbors": dup_sids or [],
           "dup_known_neighbor": "",
           "match_name": "", "match_otype": "", "match_rule": "",
           "match_sep_as": "", "t_implied": "", "margin": ""}
    if dup_sids:
        rec["status"] = "D"
        for d in dup_sids:
            if d != sid and d in known_ids:
                rec["dup_known_neighbor"] = d
                break
    best, margin = evaluate_hits(hits, cand, pm)
    if best:
        rec["status"] = "K"
        rec["match_name"] = best["name"][:40]
        rec["match_otype"] = best["otype"]
        rec["match_rule"] = best["rule"]
        rec["match_sep_as"] = best["match_sep_as"]
        rec["t_implied"] = best["t_implied"] if best["t_implied"] is not None else ""
    elif sid in known_ids:
        rec["status"] = "K"
        rec["match_rule"] = "source-id"
    else:
        rec["status"] = "P"
    if margin is not None:
        rec["margin"] = round(margin, 2)
    return rec


QLOG_LIST = []  # module-level; flushed incrementally (append mode)
_QLOG_WRITTEN = 0  # per-process counter; new processes append to the file


def flush_qlog():
    global _QLOG_WRITTEN
    new = QLOG_LIST[_QLOG_WRITTEN:]
    if not new:
        return
    exists = os.path.exists(QLOG) and os.path.getsize(QLOG) > 0
    with open(QLOG, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["ts", "phase", "sid", "ra", "dec",
                                          "svc", "n", "s", "err"])
        if not exists:
            w.writeheader()
        w.writerows(new)
    _QLOG_WRITTEN = len(QLOG_LIST)


def run_pool(cands, worker, state, flush_every=25, done_key=None):
    """Run worker(cand) over pending candidates with 2 threads; checkpoint.
    done_key: state marker added by the worker; if set, candidates whose
    state record already carries it are skipped (resume support)."""
    def pending_list():
        return [c for c in cands
                if done_key is None or done_key not in state.get(c["source_id"], {})]
    pending = pending_list()
    print(f"{len(pending)} to do ({len(state)} checkpointed)", flush=True)
    done = 0
    with ThreadPoolExecutor(max_workers=N_THREADS) as ex:
        for cand, rec in ex.map(worker, pending):
            state[cand["source_id"]] = rec
            done += 1
            if done % flush_every == 0:
                json.dump(state, open(STATE, "w"))
                flush_qlog()
                print(f"{done}/{len(pending)} done", flush=True)
    json.dump(state, open(STATE, "w"))
    flush_qlog()


def phase_sweep(cands, grid, known_ids):
    state = json.load(open(STATE)) if os.path.exists(STATE) else {}
    for _pass in range(3):  # retry failed lookups up to 2 extra passes
        failed = [k for k, v in state.items() if v.get("status") == "F"]
        for k in failed:
            del state[k]

        def worker(cand):
            sid = cand["source_id"]
            ra, dec = float(cand["ra"]), float(cand["dec"])
            pmra, pmdec = float(cand["pmra"]), float(cand["pmdec"])
            pm = math.hypot(pmra, pmdec)
            ra2000, dec2000 = propagate(ra, dec, pmra, pmdec, EPOCH_CAT - EPOCH_GAIA)
            rec = {"ra2000": ra2000, "dec2000": dec2000, "pm_tot": round(pm, 1)}
            dup = [s for s in harvest_neighbors(grid, ra, dec) if s != sid]
            try:
                hits, dt = simbad_cone(ra2000, dec2000, "A", sid)
                QLOG_LIST.append({"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                  "phase": "A", "sid": sid, "ra": round(ra2000, 5),
                                  "dec": round(dec2000, 5), "svc": "simbad-cfa",
                                  "n": len(hits), "s": round(dt, 2)})
                rec.update(match_and_classify(cand, hits, pm, dup, known_ids))
                rec["n_hits"] = len(hits)
            except Exception as e:
                rec["status"] = "F"
                rec["error"] = str(e)[:120]
                QLOG_LIST.append({"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                  "phase": "A", "sid": sid, "ra": round(ra2000, 5),
                                  "dec": round(dec2000, 5), "svc": "simbad-cfa",
                                  "n": -1, "s": "", "err": str(e)[:80]})
            return cand, rec

        run_pool(cands, worker, state)
        if not any(v.get("status") == "F" for v in state.values()):
            break
    counts = {}
    for r in state.values():
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    print("sweep counts:", counts, flush=True)
    return state


def phase_survivors(cands, grid, known_ids, meta):
    state = json.load(open(STATE)) if os.path.exists(STATE) else {}
    surv = [c for c in cands if state.get(c["source_id"], {}).get("status") == "P"]
    for i, c in enumerate(surv, 1):
        c["_h_rank"] = i  # H-rank among survivors (candidates.csv is H-sorted)
    print(f"survivors to deep-vet: {len(surv)}", flush=True)
    # IRSA CatWISE cone queries cost ~13 s each (big catalog, per-cone index);
    # run them only for the top-N shortlist-bound survivors by H rank and
    # GCNS cones alongside. Others record wise_check='skipped(>top-N)'.
    CATWISE_TOP_N = 50

    def worker(cand):
        sid = cand["source_id"]
        ra, dec = float(cand["ra"]), float(cand["dec"])
        pmra, pmdec = float(cand["pmra"]), float(cand["pmdec"])
        pm = math.hypot(pmra, pmdec)
        rec = dict(state[sid])
        ranow, decnow = propagate(ra, dec, pmra, pmdec, EPOCH_NOW - EPOCH_GAIA)
        raw15, dec15 = propagate(ra, dec, pmra, pmdec, EPOCH_WISE - EPOCH_GAIA)
        rec["ranow"], rec["decnow"] = ranow, decnow
        # B: second SIMBAD cone at present-day position
        try:
            hits, dt = simbad_cone(ranow, decnow, "B", sid)
            QLOG_LIST.append({"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                         "phase": "B", "sid": sid, "ra": round(ranow, 5),
                         "dec": round(decnow, 5), "svc": "simbad-cfa",
                         "n": len(hits), "s": round(dt, 2)})
            best, margin = evaluate_hits(hits, cand, pm)
            if best:
                rec["status"] = "K"
                rec["match_name"] = best["name"][:40]
                rec["match_otype"] = best["otype"]
                rec["match_rule"] = best["rule"] + "@now"
                rec["match_sep_as"] = best["match_sep_as"]
            elif margin is not None and (rec["margin"] == "" or margin < float(rec["margin"])):
                rec["margin"] = round(margin, 2)
            rec["n_hits_now"] = len(hits)
        except Exception as e:
            rec["b_error"] = str(e)[:120]
        # C: SIMBAD ident check for the Gaia DR3/EDR3 id itself
        try:
            q = (f"SELECT TOP 3 i.id, b.main_id, b.otype FROM ident AS i "
                 f"JOIN basic AS b ON i.oidref = b.oid WHERE i.id IN "
                 f"('Gaia DR3 {sid}','Gaia EDR3 {sid}')")
            body, dt = tap(SIMBAD_URL, q)
            rows = parse_csv(body)[1:]
            QLOG_LIST.append({"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                         "phase": "C", "sid": sid, "ra": "", "dec": "",
                         "svc": "simbad-ident", "n": len(rows), "s": round(dt, 2)})
            rec["ident"] = rows[0][0].strip('"') if rows else "none"
            if rows and rec["status"] == "P":
                rec["status"] = "K"
                rec["match_name"] = rows[0][1].strip('"')[:40]
                rec["match_otype"] = rows[0][2].strip('"')
                rec["match_rule"] = "ident"
        except Exception as e:
            rec["c_error"] = str(e)[:120]
        # E: IRSA CatWISE2020 cone at the epoch-2015.5 position (top-N only)
        if cand.get("_h_rank", 10**9) <= CATWISE_TOP_N:
            try:
                rad = max(8.0, TOL_K * pm * (EPOCH_GAIA - EPOCH_WISE) / 1000.0) / 3600.0
                hits, dt = irsa_cone(raw15, dec15, rad, sid)
                QLOG_LIST.append({"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                             "phase": "E", "sid": sid, "ra": round(raw15, 5),
                             "dec": round(dec15, 5), "svc": "irsa-catwise",
                             "n": len(hits), "s": round(dt, 2)})
                cw = hits[0] if hits and hits[0]["sep_as"] < max(3.5, TOL_K * pm * 0.5 / 1000.0 + 2.0) else None
                if cw:
                    rec["cw_id"], rec["cw_sep_as"] = cw["cw_id"], cw["sep_as"]
                    rec["cw_w1w2"] = (round(cw["w1mpro"] - cw["w2mpro"], 2)
                                      if cw.get("w1mpro") is not None and cw.get("w2mpro") is not None else "")
                    if cw.get("pmra") is not None:
                        cwpm = (math.hypot(cw["pmra"], cw["pmdec"]) * 1000.0)  # deg/yr -> mas/yr
                        rec["cw_pm_mas"] = round(cwpm, 1)
                        rec["cw_pm_ratio"] = round(cwpm / pm, 2) if pm > 0 else ""
                rec["wise"] = "catwise-match" if cw else "no-catwise-match"
            except Exception as e:
                rec["wise"] = "failed"
                rec["e_error"] = str(e)[:120]
        else:
            rec["wise"] = f"skipped(rank>{CATWISE_TOP_N}; IRSA cone ~13s/q)"
        # D: G-VO GCNS 5' cone at the 2016.0 position (top-N only)
        if cand.get("_h_rank", 10**9) <= CATWISE_TOP_N:
            try:
                hits, dt = gvo_cone(ra, dec, sid)
                QLOG_LIST.append({"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                             "phase": "D", "sid": sid, "ra": ra, "dec": dec,
                             "svc": "gvo-gcns", "n": len(hits), "s": round(dt, 2)})
                near = [h for h in hits if h["sep_as"] < 10.0]
                rec["gcns_near"] = ("none-within-10as" if not near else
                                    f"{near[0]['source_id']}@{near[0]['sep_as']}as")
            except Exception as e:
                rec["gcns_near"] = f"failed: {str(e)[:60]}"
        # parallax quality from the harvest
        pe = meta.get(sid, ("",))[0]
        try:
            plx = float(cand["parallax"])
            rec["plx_sn"] = round(plx / float(pe), 1) if pe else ""
        except (ValueError, ZeroDivisionError):
            rec["plx_sn"] = ""
        return cand, rec

    run_pool(surv, worker, state, done_key="wise")
    remain = sum(1 for r in state.values() if r.get("status") == "P")
    print(f"possible-new after deep vetting: {remain}", flush=True)
    return state


def phase_gcns_shortlist(cands, state, shortlist_ids):
    """G-VO GCNS 5' cone at the 2016.0 position, for the final shortlist."""
    for sid in shortlist_ids:
        rec = state.get(sid)
        if not rec or "gcns_near" in rec:
            continue
        cand = next(c for c in cands if c["source_id"] == sid)
        ra, dec = float(cand["ra"]), float(cand["dec"])
        try:
            hits, dt = gvo_cone(ra, dec, sid)
            QLOG_LIST.append({"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                         "phase": "D", "sid": sid, "ra": ra, "dec": dec,
                         "svc": "gvo-gcns", "n": len(hits), "s": round(dt, 2)})
            near = [h for h in hits if h["sep_as"] < 10.0]
            rec["gcns_near"] = ("none-within-10as" if not near else
                                f"{near[0]['source_id']}@{near[0]['sep_as']}as")
        except Exception as e:
            rec["gcns_near"] = f"failed: {str(e)[:60]}"
        time.sleep(0.3)
    json.dump(state, open(STATE, "w"))
    flush_qlog()


def finalize(cands, state, meta):
    """Confidence classes for possible-new rows:
       C  ambiguous  : nearest non-matching SIMBAD hit within 2x tolerance
                       (margin < 2), or corr-old/corridor match involved,
                       or CatWISE PM wildly inconsistent (ratio <0.5 or >2),
                       or parallax S/N < 5
       A  high       : margin >= 2 in both cones, no ident, no GCNS hit,
                       CatWISE matched with consistent PM (or CW absent noted),
                       parallax S/N >= 5, bp_rp >= 2.6
       B  needs eyes : everything in between (incl. failed WISE/ident checks)
    """
    order = {c["source_id"]: i for i, c in enumerate(cands)}
    fields = ["rank", "source_id", "ra", "dec", "ra2000", "dec2000",
              "pm_tot", "parallax", "plx_sn", "dist_pc", "G", "bp_rp",
              "H_rpm", "ruwe", "status", "match_name", "match_otype",
              "match_rule", "match_sep_as", "t_implied", "margin",
              "n_hits", "n_hits_now", "dup_neighbors",
              "dup_known_neighbor", "ident", "wise", "cw_id", "cw_sep_as",
              "cw_w1w2", "cw_pm_mas", "cw_pm_ratio", "gcns_near",
              "ls_cutout", "lit_check", "conf"]
    out = []
    for sid, rec in state.items():
        if rec.get("status") == "F":
            rec = dict(rec)
            # retry semantics: failed rows stay failed, never possible-new
        c = next((x for x in cands if x["source_id"] == sid), None)
        row = {k: "" for k in fields}
        if c:
            row.update({"rank": order[sid] + 1, "source_id": sid,
                        "ra": round(float(c["ra"]), 5), "dec": round(float(c["dec"]), 5),
                        "parallax": c["parallax"], "dist_pc": c["dist_pc"],
                        "G": round(float(c["G"]), 2), "bp_rp": round(float(c["bp_rp"]), 2),
                        "H_rpm": c["H_rpm"], "ruwe": c["ruwe"]})
        row.update({k: rec.get(k, "") for k in fields if k in rec})
        row["ra2000"] = round(rec.get("ra2000", 0), 5) if "ra2000" in rec else ""
        row["dec2000"] = round(rec.get("dec2000", 0), 5) if "dec2000" in rec else ""
        conf = ""
        if rec.get("status") == "P":
            margin = float(rec["margin"]) if rec.get("margin") != "" else 99.0
            plxsn = float(rec["plx_sn"]) if rec.get("plx_sn") != "" else 0.0
            ratio = float(rec["cw_pm_ratio"]) if rec.get("cw_pm_ratio") not in ("", None) else None
            bp_rp = float(row["bp_rp"]) if row["bp_rp"] != "" else 9.9
            rules = rec.get("match_rule", "")
            bad_pm = ratio is not None and (ratio < 0.5 or ratio > 2.0)
            if margin < 2.0 or "corr-old" in rules or bad_pm or plxsn < 5.0:
                conf = "C"
            elif (margin >= 2.0 and rec.get("ident") in ("none", "") and
                  rec.get("gcns_near", "") == "none-within-10as" and
                  rec.get("wise") == "catwise-match" and not bad_pm and
                  plxsn >= 5.0 and bp_rp >= 2.6):
                conf = "A"
            else:
                conf = "B"
        row["conf"] = conf
        out.append(row)
    out.sort(key=lambda r: (int(r["rank"]) if r["rank"] != "" else 9999,
                            r["source_id"]))
    # full-fidelity lab file (git renders come from render_git_csvs.py):
    # ranks 1..1000 in vetting_v2.csv, overflow to vetting_v2_tail.csv
    SPLIT_AT = 1000
    path = os.path.join(RES, "vetting_v2.csv")
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(out[:SPLIT_AT])
    counts = {}
    confs = {}
    for r in out:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
        if r["status"] == "P":
            confs[r["conf"]] = confs.get(r["conf"], 0) + 1
    print(f"vetting_v2.csv: {len(out[:SPLIT_AT])} rows "
          f"({os.path.getsize(path)} bytes); status {counts}; conf {confs}")
    if len(out) > SPLIT_AT:
        tpath = os.path.join(RES, "vetting_v2_tail.csv")
        with open(tpath, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(out[SPLIT_AT:])
        print(f"vetting_v2_tail.csv: {len(out) - SPLIT_AT} rows "
              f"({os.path.getsize(tpath)} bytes)")

    # --- results/possible_new_final.csv: one row per POSSIBLE-NEW survivor ---
    pf_fields = ["source_id", "ra2016", "dec2016", "ra2000", "dec2000", "ranow",
                 "decnow", "pm_tot", "parallax", "plx_sn", "dist_pc", "G",
                 "bp_rp", "H_rpm", "ruwe", "simbad_hits_ep2000", "simbad_hits_now",
                 "simbad_match", "margin_x", "ident_check", "wise_check",
                 "gcns_check", "ls_cutout", "lit_check", "confidence"]
    pf = []
    for r in out:
        if r["status"] != "P":
            continue
        match = (f'{r["match_name"]}({r["match_otype"]}) rule={r["match_rule"]}'
                 f' sep={r["match_sep_as"]}as' if r["match_name"] else "none")
        c = next(x for x in cands if x["source_id"] == r["source_id"])
        ranow, decnow = propagate(float(c["ra"]), float(c["dec"]),
                                  float(c["pmra"]), float(c["pmdec"]),
                                  EPOCH_NOW - EPOCH_GAIA)
        pf.append({
            "source_id": r["source_id"], "ra2016": r["ra"], "dec2016": r["dec"],
            "ra2000": r["ra2000"], "dec2000": r["dec2000"],
            "ranow": round(ranow, 5), "decnow": round(decnow, 5),
            "pm_tot": r["pm_tot"], "parallax": r["parallax"],
            "plx_sn": r["plx_sn"], "dist_pc": r["dist_pc"], "G": r["G"],
            "bp_rp": r["bp_rp"], "H_rpm": r["H_rpm"], "ruwe": r["ruwe"],
            "simbad_hits_ep2000": r.get("n_hits", ""),
            "simbad_hits_now": r.get("n_hits_now", ""),
            "simbad_match": match, "margin_x": r["margin"],
            "ident_check": r.get("ident", "not-run"),
            "wise_check": r.get("wise", "not-run"),
            "gcns_check": r.get("gcns_near", "not-run"),
            "ls_cutout": r.get("ls_cutout", "not-run"),
            "lit_check": r.get("lit_check", "unsearched"),
            "confidence": r["conf"],
        })
    pf.sort(key=lambda r: float(r["H_rpm"]) if r["H_rpm"] != "" else 0.0, reverse=True)
    ppath = os.path.join(RES, "possible_new_final.csv")
    with open(ppath, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=pf_fields)
        w.writeheader()
        w.writerows(pf)
    print(f"possible_new_final.csv: {len(pf)} survivors -> {ppath} "
          f"({os.path.getsize(ppath)} bytes)")
    return out, counts, confs


def main():
    phase = sys.argv[1] if len(sys.argv) > 1 else "all"
    cands = load_candidates()
    grid, meta = load_harvest_grid()
    known = set()
    for fn in ("gcns_sources.txt", "kirkpatrick2024_sources.txt",
               "simbad_ucd_sources.txt"):
        p = os.path.join(RES, "known", fn)
        with open(p) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    known.add(line)
    print(f"candidates: {len(cands)}, harvest grid: "
          f"{sum(len(v) for v in grid.values())}, known ids: {len(known)}")
    if phase in ("sweep", "all"):
        state = phase_sweep(cands, grid, known)
    else:
        state = json.load(open(STATE))
    if phase in ("survivors", "all"):
        state = phase_survivors(cands, grid, known, meta)
    if phase in ("finalize", "all"):
        rows, counts, confs = finalize(cands, state, meta)
        shortlist = [r["source_id"] for r in rows if r["status"] == "P"][:40]
        state = json.load(open(STATE))
        phase_gcns_shortlist(cands, state, shortlist)
        rows, counts, confs = finalize(cands, state, meta)
    flush_qlog()


if __name__ == "__main__":
    main()
