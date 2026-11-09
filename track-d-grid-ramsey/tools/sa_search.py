#!/usr/bin/env python3
"""sa_search.py — heuristic upper-bound search for the minimum number of
monochromatic rectangles in an m x n grid 2-coloring.

Objective computed EXACTLY the same way the CP-SAT count model does:
mono = sum over row pairs of [C(a00,2)+C(a11,2)] where a00/a11 count
columns where the pair agrees on 0 / on 1.  Every reported grid is
re-counted with an independent corner-based counter before printing.

12 independent annealing processes (one per core), bounded runtime.
Result on 9x9 (100 s): best verified 104 — NOT competitive with CP-SAT
(80); kept for the record per lab principle 3 (negative results).

Usage: python3 sa_search.py m n --time 90 [--json OUT]
"""
import argparse
import json
import multiprocessing as mp
import random
import time


def mono_count(cells, m, n):
    # independent validator (corner-based)
    cnt = 0
    for r1 in range(m):
        for r2 in range(r1 + 1, m):
            for c1 in range(n):
                for c2 in range(c1 + 1, n):
                    v = cells[r1][c1]
                    if v == cells[r1][c2] == cells[r2][c1] == cells[r2][c2]:
                        cnt += 1
    return cnt


def pair_costs(cells, m, n):
    """a00[i][j], a11[i][j] for i<j; objective = sum C(a00,2)+C(a11,2)."""
    a00 = [[0] * m for _ in range(m)]
    a11 = [[0] * m for _ in range(m)]
    for i in range(m):
        for j in range(i + 1, m):
            s0 = s1 = 0
            for c in range(n):
                if cells[i][c] == 0 and cells[j][c] == 0:
                    s0 += 1
                elif cells[i][c] == 1 and cells[j][c] == 1:
                    s1 += 1
            a00[i][j] = a00[j][i] = s0
            a11[i][j] = a11[j][i] = s1
    return a00, a11


def objective(a00, a11, m):
    o = 0
    for i in range(m):
        for j in range(i + 1, m):
            o += a00[i][j] * (a00[i][j] - 1) // 2
            o += a11[i][j] * (a11[i][j] - 1) // 2
    return o


def anneal(seed, m, n, deadline, out_q, t_start):
    rng = random.Random(seed)
    cells = [[rng.randint(0, 1) for _ in range(n)] for _ in range(m)]
    # balance colors per row
    for r in range(m):
        row = cells[r]
        while sum(row) > n // 2 + (n % 2):
            idx = rng.choice([c for c in range(n) if row[c]])
            row[idx] = 0
        while sum(row) < n // 2:
            idx = rng.choice([c for c in range(n) if not row[c]])
            row[idx] = 1
    a00, a11 = pair_costs(cells, m, n)
    cur = objective(a00, a11, m)
    best, best_cells = cur, [row[:] for row in cells]
    T0, T1 = 6.0, 0.05
    steps = 0
    while time.time() < deadline:
        steps += 1
        frac = (deadline - time.time()) / max(deadline - t_start, 1e-9)
        T = T1 + (T0 - T1) * max(frac, 0.0)
        r = rng.randrange(m)
        c = rng.randrange(n)
        old = cells[r][c]
        delta = 0
        touched = []
        for j in range(m):
            if j == r:
                continue
            i, jj = min(r, j), max(r, j)
            a0, a1 = a00[i][jj], a11[i][jj]
            if old == 0:  # 0->1: a00 -=1, a11 +=1
                delta += (a0 - 1) + a1  # C(a0-1,2)-C(a0,2) = -(a0-1)
                touched.append((i, jj, -1, +1))
            else:  # 1->0
                delta += a0 + (a1 - 1)
                touched.append((i, jj, +1, -1))
        if delta <= 0 or rng.random() < pow(2.718281828, -delta / T):
            cells[r][c] = 1 - old
            for (i, jj, d0, d1) in touched:
                a00[i][jj] += d0
                a11[i][jj] += d1
            cur += delta
            if cur < best:
                best = cur
                best_cells = [row[:] for row in cells]
    out_q.put((best, best_cells, steps))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("m", type=int)
    ap.add_argument("n", type=int)
    ap.add_argument("--time", type=float, default=90.0)
    ap.add_argument("--json", type=str, default=None)
    args = ap.parse_args()
    t_start = time.time()
    deadline = t_start + args.time
    out_q = mp.Queue()
    procs = [
        mp.Process(target=anneal,
                   args=(1000 + s, args.m, args.n, deadline, out_q, t_start))
        for s in range(mp.cpu_count())
    ]
    for p in procs:
        p.start()
    results = [out_q.get() for _ in procs]
    for p in procs:
        p.join()
    best, cells, steps = min(results, key=lambda t: t[0])
    m, n = args.m, args.n
    verified = mono_count(cells, m, n)
    print(json.dumps({
        "m": m, "n": n, "best_cost": best, "verified": verified,
        "steps_per_proc": steps,
    }))
    for row in cells:
        print("".join("#" if v else "." for v in row))
    if args.json and verified == best:
        with open(args.json, "w") as f:
            json.dump({"m": m, "n": n, "objective": best,
                       "grid": cells}, f)
