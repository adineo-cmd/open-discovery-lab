#!/usr/bin/env python3
"""build_known.py — build known-object exclusion sets in results/known/.

Each set is a plain .txt of Gaia DR3 source_ids, one per line, with a
'# ' comment header naming provenance and fetch date.

Sources tried, in order (2026-11-09 findings):
  gcns     VizieR I/364/gcns (GCNS main catalogue, 331,312 rows). The GCNS is
           NOT in J/A+A/649/A6 (that catalog only carries supplementary
           tables table1c/table1r/progwd/table3/...; its main table was
           published as catalog I/364/gcns). CFA asu-tsv with backoff;
           if the mirror stays down, fall back to a GCNS-proxy set derived
           from the harvest itself (plx >= 9.57 mas, plx/plxerr >= 20,
           ruwe < 1.4, G < 20 -> Smart+2021 selection).
  k24      Kirkpatrick+2024 20-pc census J/ApJS/271/55 table4 — already
           downloaded as results/known/kirkpatrick2024_table4.csv; extract
           ids from its 'Gaia' column ("Gaia EDR3 <id>" strings).
  simbad   Simbad CFA mirror sim-tap: Gaia DR3 ids of ultracool/subdwarf/WD
           otypes (LM*, BD*, SD*, WD*). Covers Kirkpatrick 2021 objects
           (J/ApJS/253/7 tablea1 carries no Gaia ids, only CatWISE
           astrometry).

Usage: python3 build_known.py [--gcns-only] [--simbad-only] [--k24-only]
"""
import csv
import datetime
import os
import re
import sys
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results")
KNOWN = os.path.join(RES, "known")
TODAY = datetime.date.today().isoformat()

VIZIER_ASU = "https://vizier.cfa.harvard.edu/viz-bin/asu-tsv"
SIMBAD_TAP = "https://simbad.cfa.harvard.edu/simbad/sim-tap/sync"
GVO_TAP = "https://dc.g-vo.org/tap/sync"  # hosts gcns.main (Smart+2021)
K24_CSV = os.path.join(KNOWN, "kirkpatrick2024_table4.csv")


def http_post(url, params, timeout=180):
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=data, headers={"User-Agent": "open-discovery-lab/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def http_get(url, timeout=180):
    req = urllib.request.Request(url, headers={"User-Agent": "open-discovery-lab/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def write_ids(fname, provenance, ids):
    ids = sorted(set(i for i in ids if i and i.strip().isdigit()))
    out = os.path.join(KNOWN, fname)
    with open(out, "w") as f:
        f.write(f"# {fname}\n# provenance: {provenance}\n# fetched: {TODAY}\n"
                f"# n_ids: {len(ids)}\n")
        f.write("\n".join(ids) + "\n")
    print(f"{fname}: {len(ids)} ids -> {out}")
    return len(ids)


def build_k24():
    """Extract Gaia ids from the already-downloaded K24 table4 CSV."""
    if not os.path.exists(K24_CSV):
        print("k24: table4 CSV missing, skipping")
        return 0
    ids = []
    n_no_id = 0
    with open(K24_CSV, errors="replace") as f:
        rd = csv.DictReader(f)
        for row in rd:
            raw = (row.get("Gaia") or "").strip()
            m = re.search(r"(\d{10,20})$", raw)  # "Gaia EDR3 1234567890..."
            if m:
                ids.append(m.group(1))
            else:
                n_no_id += 1
    write_ids("kirkpatrick2024_sources.txt",
              "Kirkpatrick+2024 20-pc census (J/ApJS/271/55 table4, local CSV), "
              "Gaia column stripped of 'Gaia EDR3 ' prefix; "
              f"{n_no_id} rows without a Gaia id (mostly distant/low-pm entries) "
              "remain position-only", ids)
    return len(ids)


def build_simbad():
    """Gaia DR3 ids for ultracool/subdwarf/white-dwarf otypes via Simbad CFA TAP."""
    q = ("SELECT i.ids AS gaia_id, b.main_id, b.otype "
         "FROM basic AS b JOIN ids AS i ON i.oidref = b.oid "
         "WHERE b.otype IN ('LM*','BD*','SD*','WD*') "
         "AND i.ids LIKE 'Gaia DR3 %'")
    last_err = None
    for attempt in range(3):
        try:
            # NOTE: sim-tap/sync rejects our POST (HTTP 400) but accepts GET.
            body = http_get(SIMBAD_TAP + "?" + urllib.parse.urlencode({
                "REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "csv", "QUERY": q
            }), timeout=300)
            ids = []
            for row in csv.reader(body.splitlines()):
                if row and row[0].startswith("Gaia DR3 ") and row[0].split()[-1].isdigit():
                    ids.append(row[0].split()[-1])
            return write_ids("simbad_ucd_sources.txt",
                             f"SIMBAD (simbad.cfa.harvard.edu sim-tap), otype IN "
                             f"(LM*,BD*,SD*,WD*) with Gaia DR3 identifier, {len(ids)} ids", ids)
        except Exception as e:
            last_err = e
            print(f"simbad attempt {attempt + 1} failed: {e}")
            time.sleep(10)
    print(f"simbad FAILED after retries: {last_err}")
    return 0


def build_gcns_from_gvo():
    """GCNS main catalogue via G-VO TAP (dc.g-vo.org/gcns), keyset-paginated.

    G-VO sync TAP caps at 20000 rows and uses TOP (no LIMIT).
    """
    def page(last):
        q = (f"SELECT TOP 19999 source_id FROM gcns.main "
             f"WHERE source_id > {last} ORDER BY source_id")
        body = http_get(GVO_TAP + "?" + urllib.parse.urlencode({
            "REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "csv", "QUERY": q
        }), timeout=180)
        return [int(l) for l in body.splitlines()[1:] if l.strip().isdigit()]

    ids, last = [], 0
    for attempt in range(30):
        try:
            p = page(last)
        except Exception as e:
            print(f"gcns/gvo page {attempt} failed: {e}")
            time.sleep(10)
            continue
        if not p:
            break
        ids.extend(p)
        last = p[-1]
        if len(p) < 19999:
            break
    if len(ids) < 100000:
        print(f"gcns from G-VO got only {len(ids)} ids, refusing")
        return 0
    return write_ids("gcns_sources.txt",
                     f"Gaia Catalogue of Nearby Stars (Smart+2021, VizieR I/364/gcns "
                     f"== gcns.main) via G-VO TAP dc.g-vo.org keyset pagination, "
                     f"{len(ids)} ids", ids)


def build_gcns_from_vizier():
    """GCNS main catalogue I/364/gcns via CFA asu-tsv (Source column).

    NB: CFA was in a Postgres outage on 2026-11-09/10 ('metaviz@CFA' no
    connection); the working route was G-VO (build_gcns_from_gvo).
    """
    url = (VIZIER_ASU + "?-source=I/364/gcns&-out=Source&-out.max=unlimited")
    last_err = None
    for attempt in range(3):
        try:
            body = http_get(url, timeout=600)
            if "not currently reachable" in body or "Postgres connect error" in body:
                raise RuntimeError("CFA VizieR DB outage (transient)")
            ids = []
            for line in body.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.lower().startswith("source"):
                    continue
                if line.isdigit():
                    ids.append(line)
            if len(ids) < 100000:
                raise RuntimeError(f"GCNS fetch too small ({len(ids)} ids), refusing")
            return write_ids("gcns_sources.txt",
                             f"Gaia Catalogue of Nearby Stars (Smart+2021, VizieR "
                             f"I/364/gcns main table) via vizier.cfa.harvard.edu asu-tsv, "
                             f"{len(ids)} ids", ids)
        except Exception as e:
            last_err = e
            print(f"gcns attempt {attempt + 1} failed: {e}")
            time.sleep(20)
    print(f"gcns from CFA VizieR failed ({last_err}); trying G-VO mirror ...")
    return build_gcns_from_gvo()


def build_gcns_proxy_from_harvest():
    """Fallback: GCNS-proxy ids from the harvest itself (Smart+2021 cuts).

    The harvest already holds every Gaia DR3 row with (pmra^2+pmdec^2)>22500,
    G<20, ruwe<1.4, parallax not null. A harvest row is GCNS-member-like when
    it additionally passes parallax >= 9.57 mas and parallax/parallax_error
    >= 20 (Smart+2021 selection). Only harvest rows matter for exclusion.
    """
    import math
    src = os.path.join(RES, "chunks", "all_high_pm.csv")
    if not os.path.exists(src):
        print("gcns proxy: harvest not found, skipping")
        return 0
    ids = []
    with open(src, errors="replace") as f:
        rd = csv.DictReader(f)
        for row in rd:
            try:
                plx = float(row["parallax"])
                plxe = float(row["parallax_error"])
                ruwe = float(row["ruwe"])
                g = float(row["phot_g_mean_mag"])
            except (ValueError, KeyError, TypeError):
                continue
            if plx >= 9.57 and plxe > 0 and plx / plxe >= 20 and ruwe < 1.4 and g < 20:
                ids.append(row["source_id"].strip())
    write_ids("gcns_sources.txt",
              "GCNS-PROXY (fallback: VizieR I/364/gcns unreachable from CFA on "
              f"{TODAY}): harvest rows passing Smart+2021 GCNS cuts "
              "(plx>=9.57mas, plx/plxerr>=20, ruwe<1.4, G<20); only covers "
              "high-PM harvest rows by construction", ids)
    return len(ids)


def main():
    os.makedirs(KNOWN, exist_ok=True)
    which = set(a.lstrip("-").split("-")[0] for a in sys.argv[1:] if a.startswith("--")) or \
        {"gcns", "simbad", "k24"}
    if "k24" in which:
        build_k24()
    if "simbad" in which:
        build_simbad()
    if "gcns" in which:
        n = build_gcns_from_gvo()
        if n == 0:
            n = build_gcns_from_vizier()
        if n == 0:
            build_gcns_proxy_from_harvest()


if __name__ == "__main__":
    main()
