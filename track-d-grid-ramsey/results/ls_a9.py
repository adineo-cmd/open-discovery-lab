#!/usr/bin/env python3
"""ls_a9.py -- iterated local search (ILS) for min mono rectangles, 9x9.

State = grid + incremental per-row-pair (a00, a11) counts and pair mono
counts.  Move set: single cell flips (delta O(9)), whole-row flips and
whole-column flips (delta O(36)).  Strict descent to local optimum, then
random kicks (cell-flip bursts / row or column flips / row re-randomization),
re-descend, keep global best.  Every new global best is re-counted by the
independent pure-Python corner counter before being recorded.
"""
import json
import random
import sys
import time

M = N = 9


def count_mono(cells, m=M, n=N):
    cnt = 0
    for r1 in range(m):
        for r2 in range(r1 + 1, m):
            for c1 in range(n):
                for c2 in range(c1 + 1, n):
                    if cells[r1][c1] == cells[r1][c2] == cells[r2][c1] == cells[r2][c2]:
                        cnt += 1
    return cnt


class State:
    __slots__ = ("g", "a00", "a11", "mono", "total", "zrow", "zcol")

    def __init__(self, grid):
        self.g = [row[:] for row in grid]
        self.a00 = [[0] * M for _ in range(M)]
        self.a11 = [[0] * M for _ in range(M)]
        self.mono = [[0] * M for _ in range(M)]
        self.recalc()

    def recalc(self):
        g = self.g
        self.zrow = [M - sum(r) for r in g]   # zeros per row
        self.zcol = [sum(1 for r in range(M) if g[r][c] == 0) for c in range(N)]
        self.total = 0
        for i in range(M):
            for j in range(i + 1, M):
                a00 = a11 = 0
                gi, gj = g[i], g[j]
                for c in range(N):
                    if gi[c]:
                        if gj[c]:
                            a11 += 1
                    elif not gj[c]:
                        a00 += 1
                self.a00[i][j] = self.a00[j][i] = a00
                self.a11[i][j] = self.a11[j][i] = a11
                mo = a00 * (a00 - 1) // 2 + a11 * (a11 - 1) // 2
                self.mono[i][j] = self.mono[j][i] = mo
                self.total += mo

    def apply_cell(self, r, c):
        v = self.g[r][c]
        self.g[r][c] = 1 - v
        if v:
            self.zrow[r] += 1
            self.zcol[c] += 1
        else:
            self.zrow[r] -= 1
            self.zcol[c] -= 1
        for j in range(M):
            if j == r:
                continue
            w = self.g[j][c]
            a00 = self.a00[r][j]
            a11 = self.a11[r][j]
            if v == 0:
                if w == 0:
                    d = -(a00 - 1)
                    a00 -= 1
                else:
                    d = a11
                    a11 += 1
            else:
                if w == 0:
                    d = a00
                    a00 += 1
                else:
                    d = -(a11 - 1)
                    a11 -= 1
            mo = a00 * (a00 - 1) // 2 + a11 * (a11 - 1) // 2
            self.a00[r][j] = self.a00[j][r] = a00
            self.a11[r][j] = self.a11[j][r] = a11
            self.mono[r][j] = self.mono[j][r] = mo
            self.total += d

    def apply_row(self, r):
        zj = self.zrow[r]
        for j in range(M):
            if j == r:
                continue
            a00, a11 = self.a00[r][j], self.a11[r][j]
            z = self.zrow[j]
            n00 = z - a00
            n11 = (N - z) - a11
            d = (n00 * (n00 - 1) + n11 * (n11 - 1)
                 - a00 * (a00 - 1) - a11 * (a11 - 1)) // 2
            self.a00[r][j] = self.a00[j][r] = n00
            self.a11[r][j] = self.a11[j][r] = n11
            self.mono[r][j] = self.mono[j][r] = n00 * (n00 - 1) // 2 + n11 * (n11 - 1) // 2
            self.total += d
        row = self.g[r]
        self.g[r] = [1 - v for v in row]
        for c in range(N):
            if row[c]:
                self.zcol[c] += 1
            else:
                self.zcol[c] -= 1
        self.zrow[r] = N - zj

    def apply_col(self, c):
        for i in range(M):
            for j in range(i + 1, M):
                gi, gj = self.g[i][c], self.g[j][c]
                e00 = 1 if (gi == 0 and gj == 0) else 0
                e11 = 1 if (gi == 1 and gj == 1) else 0
                if e00 or e11:
                    a00, a11 = self.a00[i][j], self.a11[i][j]
                    n00 = a00 - e00 + e11
                    n11 = a11 - e11 + e00
                    d = (n00 * (n00 - 1) - a00 * (a00 - 1)
                         + n11 * (n11 - 1) - a11 * (a11 - 1)) // 2
                    self.a00[i][j] = self.a00[j][i] = n00
                    self.a11[i][j] = self.a11[j][i] = n11
                    self.mono[i][j] = self.mono[j][i] = \
                        n00 * (n00 - 1) // 2 + n11 * (n11 - 1) // 2
                    self.total += d
        for r in range(M):
            if self.g[r][c]:
                self.zrow[r] += 1
                self.zcol[c] -= 1
            else:
                self.zrow[r] -= 1
                self.zcol[c] += 1
            self.g[r][c] = 1 - self.g[r][c]

    def cell_delta(self, r, c):
        v = self.g[r][c]
        d = 0
        for j in range(M):
            if j == r:
                continue
            w = self.g[j][c]
            if v == 0:
                d += (self.a11[r][j] if w else -(self.a00[r][j] - 1))
            else:
                d += (self.a00[r][j] if w == 0 else -(self.a11[r][j] - 1))
        return d

    def row_delta(self, r):
        d = 0
        z = self.zrow[r]
        for j in range(M):
            if j == r:
                continue
            a00, a11 = self.a00[r][j], self.a11[r][j]
            zj = self.zrow[j]
            n00 = zj - a00
            n11 = (N - zj) - a11
            d += (n00 * (n00 - 1) + n11 * (n11 - 1)
                  - a00 * (a00 - 1) - a11 * (a11 - 1)) // 2
        return d

    def col_delta(self, c):
        d = 0
        for i in range(M):
            gi = self.g[i][c]
            for j in range(i + 1, M):
                gj = self.g[j][c]
                if gi == gj:
                    a00, a11 = self.a00[i][j], self.a11[i][j]
                    if gi == 0:
                        n00, n11 = a00 - 1, a11 + 1
                    else:
                        n00, n11 = a00 + 1, a11 - 1
                    d += (n00 * (n00 - 1) - a00 * (a00 - 1)
                          + n11 * (n11 - 1) - a11 * (a11 - 1)) // 2
        return d


def descend(st, rng, max_plateau=0):
    steps = 0
    while True:
        best_d, best_mv = 0, None
        zeros = []
        for r in range(M):
            for c in range(N):
                d = st.cell_delta(r, c)
                if d < best_d:
                    best_d, best_mv = d, ("c", r, c)
                elif d == 0 and max_plateau:
                    zeros.append(("c", r, c))
        for r in range(M):
            d = st.row_delta(r)
            if d < best_d:
                best_d, best_mv = d, ("r", r)
            elif d == 0 and max_plateau:
                zeros.append(("r", r))
        for c in range(N):
            d = st.col_delta(c)
            if d < best_d:
                best_d, best_mv = d, ("C", c)
            elif d == 0 and max_plateau:
                zeros.append(("C", c))
        if best_d < 0:
            mv = best_mv
        elif max_plateau and zeros:
            mv = zeros[rng.randrange(len(zeros))]
            max_plateau -= 1
        else:
            return steps
        if mv[0] == "c":
            st.apply_cell(mv[1], mv[2])
        elif mv[0] == "r":
            st.apply_row(mv[1])
        else:
            st.apply_col(mv[1])
        steps += 1


def random_grid(rng, mode="balanced"):
    g = [[0] * N for _ in range(M)]
    if mode == "balanced":       # each column 4 or 5 ones
        for c in range(N):
            k = rng.choice((4, 5))
            rows = rng.sample(range(M), k)
            for r in rows:
                g[r][c] = 1
    elif mode == "rowbal":       # each row 4 or 5 ones
        for r in range(M):
            k = rng.choice((4, 5))
            for c in rng.sample(range(N), k):
                g[r][c] = 1
    else:                        # uniform
        for r in range(M):
            for c in range(N):
                g[r][c] = rng.randint(0, 1)
    return g


def rerand_rows(st, rng, k):
    rows = rng.sample(range(M), k)
    for r in rows:
        kk = rng.choice((4, 5))
        for c in range(N):
            st.g[r][c] = 0
        for c in rng.sample(range(N), kk):
            st.g[r][c] = 1
    st.recalc()


def main():
    ap_seed = int(sys.argv[1])
    deadline = float(sys.argv[2])
    start_file = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] != "-" else None
    out_file = sys.argv[4] if len(sys.argv) > 4 else f"ls_best_{ap_seed}.json"
    mode = sys.argv[5] if len(sys.argv) > 5 else "mix"
    rng = random.Random(ap_seed)

    if start_file:
        g0 = json.load(open(start_file))["grid"]
        if g0[0][0] == 1:
            g0 = [[1 - v for v in row] for row in g0]
        g0 = sorted(g0)
        st = State(g0)
    else:
        st = State(random_grid(rng, rng.choice(("balanced", "rowbal", "uniform"))))
    descend(st, rng)
    best_total, best_g = st.total, [r[:] for r in st.g]
    assert count_mono(best_g) == best_total
    with open(out_file, "w") as f:
        json.dump({"objective": best_total, "independent_count": best_total,
                   "seed": ap_seed, "grid": best_g, "note": "ILS best"},
                  f, indent=1)
    print(f"seed {ap_seed}: start best {best_total}", flush=True)

    it = 0
    t0 = time.time()
    while time.time() < deadline:
        it += 1
        # restore best + kick
        st = State(best_g)
        kind = rng.random()
        if mode == "mix":
            if kind < 0.45:
                k = rng.randint(2, 7)
                for _ in range(k):
                    st.apply_cell(rng.randrange(M), rng.randrange(N))
            elif kind < 0.6:
                st.apply_row(rng.randrange(M))
                for _ in range(rng.randint(1, 4)):
                    st.apply_cell(rng.randrange(M), rng.randrange(N))
            elif kind < 0.75:
                st.apply_col(rng.randrange(N))
                for _ in range(rng.randint(1, 4)):
                    st.apply_cell(rng.randrange(M), rng.randrange(N))
            else:
                rerand_rows(st, rng, rng.randint(2, 3))
        descend(st, rng, max_plateau=rng.choice((0, 0, 40)))
        if st.total < best_total:
            best_total, best_g = st.total, [r[:] for r in st.g]
            ic = count_mono(best_g)
            assert ic == best_total, (ic, best_total)
            with open(out_file, "w") as f:
                json.dump({"objective": best_total, "independent_count": ic,
                           "seed": ap_seed, "grid": best_g, "note": "ILS best",
                           "iters": it, "wall_s": round(time.time() - t0, 1)},
                          f, indent=1)
            print(f"seed {ap_seed} it {it} [{time.time()-t0:6.1f}s]: "
                  f"new best {best_total} (indep {ic})", flush=True)
        elif it % 3000 == 0:
            # periodic diversification restart
            st = State(random_grid(rng, rng.choice(("balanced", "rowbal"))))
            descend(st, rng, max_plateau=30)
            if st.total < best_total:
                best_total, best_g = st.total, [r[:] for r in st.g]
                ic = count_mono(best_g)
                with open(out_file, "w") as f:
                    json.dump({"objective": best_total,
                               "independent_count": ic, "seed": ap_seed,
                               "grid": best_g, "note": "ILS best (restart)",
                               "iters": it}, f, indent=1)
                print(f"seed {ap_seed} it {it}: restart best {best_total}",
                      flush=True)
    print(f"seed {ap_seed}: done, best {best_total}, {it} iters, "
          f"{(time.time()-t0):.0f}s", flush=True)


if __name__ == "__main__":
    main()
