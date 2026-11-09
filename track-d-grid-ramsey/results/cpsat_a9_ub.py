#!/usr/bin/env python3
"""cpsat_a9.py -- CP-SAT attack on a(9) (min mono rectangles, 9x9).

Count model v2 (per-row-pair a00/a11 with exact C(a,2) linearization),
optionally: proven-LB constraint, hard UB target constraint, witness hint,
solution callback that dumps every improving witness (independently
re-counted with a pure-Python corner counter) to --out.
"""
import argparse
import json
import sys
import time

from ortools.sat.python import cp_model


def count_mono(cells, m, n):
    cnt = 0
    for r1 in range(m):
        for r2 in range(r1 + 1, m):
            for c1 in range(n):
                for c2 in range(c1 + 1, n):
                    if cells[r1][c1] == cells[r1][c2] == cells[r2][c1] == cells[r2][c2]:
                        cnt += 1
    return cnt


def build(m, n, lb=None, ub_target=None):
    """Count model v2 (same formulation as tools/min_mono_rect.py build_count)
    but also returns the objective expression so we can add a hard UB cap."""
    model = cp_model.CpModel()
    x = {}
    for r in range(m):
        for c in range(n):
            x[r, c] = model.NewBoolVar(f"x{r}_{c}")
    obj_terms = []
    for i in range(m):
        for j in range(i + 1, m):
            p00, p11 = [], []
            for c in range(n):
                b0 = model.NewBoolVar(f"p00_{i}_{j}_{c}")
                model.AddBoolAnd([x[i, c].Not(), x[j, c].Not()]).OnlyEnforceIf(b0)
                model.AddBoolOr([x[i, c], x[j, c]]).OnlyEnforceIf(b0.Not())
                b1 = model.NewBoolVar(f"p11_{i}_{j}_{c}")
                model.AddBoolAnd([x[i, c], x[j, c]]).OnlyEnforceIf(b1)
                model.AddBoolOr([x[i, c].Not(), x[j, c].Not()]).OnlyEnforceIf(b1.Not())
                p00.append(b0)
                p11.append(b1)
            for pvars, tag in ((p00, "00"), (p11, "11")):
                a = model.NewIntVar(0, n, f"a{tag}_{i}_{j}")
                model.Add(a == sum(pvars))
                for k in range(1, n + 1):
                    u = model.NewBoolVar(f"u{tag}_{i}_{j}_{k}")
                    model.Add(a >= k).OnlyEnforceIf(u)
                    model.Add(a <= k - 1).OnlyEnforceIf(u.Not())
                    if k - 1:
                        obj_terms.append((k - 1) * u)
    obj = sum(obj_terms) if obj_terms else 0
    model.Minimize(obj)
    if lb is not None:
        model.Add(obj >= lb)
    if ub_target is not None:
        model.Add(obj <= ub_target)
    # symmetry breaking (valid: row perm + global color swap)
    model.Add(x[0, 0] == 0)
    for r in range(m - 1):
        prev_eq = None
        for c in range(n):
            if prev_eq is not None:
                model.AddBoolOr([x[r, c].Not(), x[r + 1, c], prev_eq.Not()])
            if c < n - 1:
                eqc = model.NewBoolVar(f"eq{r}_{c}")
                model.Add(x[r, c] == x[r + 1, c]).OnlyEnforceIf(eqc)
                model.Add(x[r, c] != x[r + 1, c]).OnlyEnforceIf(eqc.Not())
                if prev_eq is not None:
                    both = model.NewBoolVar("")
                    model.AddBoolAnd([prev_eq, eqc]).OnlyEnforceIf(both)
                    model.AddBoolOr([prev_eq.Not(), eqc.Not()]).OnlyEnforceIf(both.Not())
                    prev_eq = both
                else:
                    prev_eq = eqc
    return model, x, obj


class CB(cp_model.CpSolverSolutionCallback):
    def __init__(self, x, m, n, out, t0):
        super().__init__()
        self.x, self.m, self.n, self.out, self.t0 = x, m, n, out, t0
        self.best = None

    def on_solution_callback(self):
        val = int(self.ObjectiveValue())
        if self.best is not None and val >= self.best:
            return
        g = [[int(self.Value(self.x[r, c])) for c in range(self.n)]
             for r in range(self.m)]
        ic = count_mono(g, self.m, self.n)
        if ic != val:
            print(f"WARN mismatch solver={val} indep={ic}", flush=True)
            return
        self.best = val
        rec = {"objective": val, "independent_count": ic,
               "wall_s": round(time.time() - self.t0, 1), "grid": g,
               "status": "INCUMBENT"}
        with open(self.out, "w") as f:
            json.dump(rec, f, indent=1)
        print(f"[{time.time()-self.t0:7.1f}s] new incumbent {val} (indep {ic})",
              flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hint", default=None, help="json file with 'grid'")
    ap.add_argument("--lb", type=int, default=74)
    ap.add_argument("--ub-target", type=int, default=None)
    ap.add_argument("--time-limit", type=float, default=1800)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", required=True)
    ap.add_argument("--final", default=None, help="final status json out")
    args = ap.parse_args()

    m = n = 9
    model, x, obj = build(m, n, lb=args.lb, ub_target=args.ub_target)
    if args.hint:
        g = json.load(open(args.hint))["grid"]
        # hint must respect the symmetry breaking; normalize: color swap so
        # x[0][0]==0, then keep grid (row order as-is)
        if g[0][0] == 1:
            g = [[1 - v for v in row] for row in g]
        # row-lex normalize (sort rows) to satisfy symmetry breaking
        g = sorted(g)
        for r in range(m):
            for c in range(n):
                model.AddHint(x[r, c], g[r][c])

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = args.time_limit
    solver.parameters.num_search_workers = args.workers
    solver.parameters.random_seed = args.seed
    cb = CB(x, m, n, args.out, time.time())
    t0 = time.time()
    status = solver.Solve(model, cb)
    wall = time.time() - t0
    fin = {"status": solver.StatusName(status),
           "objective": int(solver.ObjectiveValue())
           if status in (cp_model.OPTIMAL, cp_model.FEASIBLE) else None,
           "bound": solver.BestObjectiveBound(),
           "wall_s": round(wall, 1), "workers": args.workers,
           "seed": args.seed, "ub_target": args.ub_target, "lb": args.lb,
           "hint": args.hint}
    print(json.dumps(fin), flush=True)
    if args.final:
        with open(args.final, "w") as f:
            json.dump(fin, f, indent=1)


if __name__ == "__main__":
    main()
