#!/usr/bin/env python3
"""apply_lit_checks.py — post-vetting evidence merge for possible-new survivors.

Steps (run AFTER `python3 vet2.py finalize`):
 1. LS-DR9 imagery check: download the 200px jpeg cutout for every
    POSSIBLE-NEW survivor into /tmp (NOT committed) and record
    ok / no-coverage / http-error in the vetting state (results/
    vetting_v2_state.json key `ls_cutout`). Blank ~1.3 kB filler tiles are
    classed as no-coverage(blank-tile): no DR9 imaging at that position.
 2. Merge manual literature notes from results/lit_check_notes.json
    (format: {"<source_id>": {"query": "...", "found": "...", "verdict":
    "unknown-in-lit" | "possible-match" | "known-in-lit", "note": "..."}})
    into the state (key `lit_check`).
 3. Re-run vet2.finalize() so results/vetting_v2.csv and
    results/possible_new_final.csv carry the imagery/literature columns.

Confidence is NOT changed here: A/B/C comes from vet2.finalize() machine
rules; literature/imagery evidence is recorded for human review.

Usage: python3 apply_lit_checks.py
"""
import json
import os
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results")
STATE = os.path.join(RES, "vetting_v2_state.json")
NOTES = os.path.join(RES, "lit_check_notes.json")
TMP = "/tmp/trackb_cutouts"
sys.path.insert(0, HERE)
import vet2  # noqa: E402


def ls_cutout_status(ra, dec):
    """Fetch the DR9 200px jpeg cutout; classify the response."""
    url = (f"https://www.legacysurvey.org/viewer/jpeg-cutout?ra={ra}&dec={dec}"
           f"&layer=ls-dr9&size=200")
    fn = os.path.join(TMP, f"{ra:.5f}_{dec:.5f}.jpg")
    for attempt in range(2):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "open-discovery-lab/0.2"})
            with urllib.request.urlopen(req, timeout=45) as r:
                data = r.read()
            if len(data) < 200 or not data.startswith(b"\xff\xd8"):
                return "no-coverage"
            if len(data) < 3000:
                # valid jpeg but ~uniform filler tile: no DR9 imaging there
                return "no-coverage(blank-tile)"
            with open(fn, "wb") as f:
                f.write(data)
            return f"ok({len(data)}b)"
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return "no-coverage"
            time.sleep(2)
        except Exception:
            time.sleep(2)
    return "http-error"


def main():
    os.makedirs(TMP, exist_ok=True)
    state = json.load(open(STATE))
    cands = {c["source_id"]: c for c in vet2.load_candidates()}
    surv = [sid for sid, r in state.items() if r.get("status") == "P"]
    print(f"survivors: {len(surv)}")
    notes = json.load(open(NOTES)) if os.path.exists(NOTES) else {}
    todo = [sid for sid in surv if "ls_cutout" not in state[sid]]
    if todo:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=4) as ex:
            futs = {ex.submit(ls_cutout_status, float(cands[sid]["ra"]),
                              float(cands[sid]["dec"])): sid for sid in todo}
            for i, (fut, sid) in enumerate(
                    ((f, s) for f, s in zip(futs, todo)), 1):
                state[sid]["ls_cutout"] = fut.result()
                if i % 100 == 0:
                    json.dump(state, open(STATE, "w"))
                    print(f"cutouts {i}/{len(todo)}", flush=True)
        json.dump(state, open(STATE, "w"))
    for sid in surv:
        if sid in notes:
            n = notes[sid]
            state[sid]["lit_check"] = f"{n.get('verdict', '?')} [{n.get('query', '')}]"
    json.dump(state, open(STATE, "w"))
    stat = {}
    for sid in surv:
        s = state[sid].get("ls_cutout", "?")
        stat[s.split("(")[0]] = stat.get(s.split("(")[0], 0) + 1
    print("ls_cutout status:", stat)
    vet2.finalize(vet2.load_candidates(), state, vet2.load_harvest_grid()[1])


if __name__ == "__main__":
    main()
