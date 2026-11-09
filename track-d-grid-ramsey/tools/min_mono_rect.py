#!/usr/bin/env python3
"""min_mono_rect.py — exact minimum number of monochromatic axis-parallel
rectangles in a 2-coloring of an m x n grid, via CP-SAT (Google OR-Tools).

A "rectangle" = choice of 2 distinct rows x 2 distinct columns; it is
monochromatic iff all 4 corner cells share one color.  This is OEIS
A399621 (triangle T(n,k): k rows x n cols) and A399620 (main diagonal).

Models (--model):
  count (default, v2)  per row-pair (i,j): mono rectangles = C(a00,2)+C(a11,2)
      where a00/a11 = #columns where rows i,j agree on 0 / on 1.  Exact
      linearization C(a,2) = sum_{k=1..a} (k-1) over reified thresholds
      u_k := (a >= k).  Small + tight LP relaxation.
  quad  (v1)           one mono bool per rectangle via 4 reified star
      equalities; kept for the record, proofs stall from n=7 up.

Symmetry breaking (valid: objective invariant under row permutation and
global color swap; column symmetry left to the solver):
  * x[0][0] = 0
  * rows lexicographically nondecreasing (equal rows allowed)

Reproducibility: CP-SAT deterministic given --workers/--seed; every
result is re-checked by an independent pure-Python counter count_mono().

Usage:
  python3 min_mono_rect.py M N [--model count|quad] [--time-limit S]
      [--workers K] [--lb LB] [--json OUT]
Prints: status, objective, proven bound, wall time, witness grid.
"""
import argparse
import json
import time

from ortools.sat.python import cp_model


def count_mono(cells, m, n):
    """Independent pure-Python counter (validator, not part of the model)."""
    cnt = 0
    for r1 in range(m):
        for r2 in range(r1 + 1, m):
            for c1 in range(n):
                for c2 in range(c1 + 1, n):
                    v = cells[r1][c1]
                    if v == cells[r1][c2] == cells[r2][c1] == cells[r2][c2]:
                        cnt += 1
    return cnt


def _and_var(model, a, b):
    v = model.NewBoolVar("and_tmp")
    model.AddBoolAnd([a, b]).OnlyEnforceIf(v)
    model.AddBoolOr([a.Not(), b.Not()]).OnlyEnforceIf(v.Not())
    return v


def build_count(m, n, lb=None):
    """v2: exact per-row-pair count formulation.  lb: proven lower bound
    from relax_lb.py added as a constraint (composition of proofs)."""
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
                # mono_pair >= C(a,2) exactly:
                #   C(a,2) = sum_{k=1..a} (k-1)  via  u_k := (a >= k)
                for k in range(1, n + 1):
                    u = model.NewBoolVar(f"u{tag}_{i}_{j}_{k}")
                    model.Add(a >= k).OnlyEnforceIf(u)
                    model.Add(a <= k - 1).OnlyEnforceIf(u.Not())
                    if k - 1:
                        obj_terms.append((k - 1) * u)
    model.Minimize(sum(t for t in obj_terms) if obj_terms else 0)
    if lb is not None:
        model.Add(sum(obj_terms) >= lb)

    # --- symmetry breaking ---
    model.Add(x[0, 0] == 0)  # color swap
    for r in range(m - 1):  # row lex order (equal rows allowed)
        prev_eq = None
        for c in range(n):
            if prev_eq is not None:
                model.AddBoolOr([x[r, c].Not(), x[r + 1, c], prev_eq.Not()])
            if c < n - 1:
                eqc = model.NewBoolVar(f"eq{r}_{c}")
                model.Add(x[r, c] == x[r + 1, c]).OnlyEnforceIf(eqc)
                model.Add(x[r, c] != x[r + 1, c]).OnlyEnforceIf(eqc.Not())
                prev_eq = eqc if prev_eq is None else _and_var(model, prev_eq, eqc)
    return model, x


def build_quad(m, n):
    """v1: one mono bool per rectangle (kept for the record)."""
    model = cp_model.CpModel()
    x = {}
    for r in range(m):
        for c in range(n):
            x[r, c] = model.NewBoolVar(f"x{r}_{c}")
    mono = []
    for r1 in range(m):
        for r2 in range(r1 + 1, m):
            for c1 in range(n):
                for c2 in range(c1 + 1, n):
                    mv = model.NewBoolVar(f"m{r1}_{r2}_{c1}_{c2}")
                    e = [model.NewBoolVar(f"e{r1}_{r2}_{c1}_{c2}_{t}")
                         for t in range(4)]
                    for val, (a, b) in zip(
                        e,
                        [(x[r1, c1], x[r1, c2]),
                         (x[r2, c1], x[r2, c2]),
                         (x[r1, c1], x[r2, c1]),
                         (x[r1, c2], x[r2, c2])]):
                        model.Add(a == b).OnlyEnforceIf(val)
                        model.Add(a != b).OnlyEnforceIf(val.Not())
                    model.AddBoolAnd(e).OnlyEnforceIf(mv)
                    model.AddBoolOr([t.Not() for t in e]).OnlyEnforceIf(mv.Not())
                    mono.append(mv)
    model.Minimize(sum(mono))
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
                prev_eq = eqc if prev_eq is None else _and_var(model, prev_eq, eqc)
    return model, x


def solve(m, n, time_limit, workers, which, lb=None):
    if which == "count":
        model, x = build_count(m, n, lb=lb)
    else:
        model, x = build_quad(m, n)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_search_workers = workers
    solver.parameters.random_seed = 20261109
    t0 = time.time()
    status = solver.Solve(model)
    wall = time.time() - t0
    ok = status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
    out = {
        "m": m, "n": n, "model": which,
        "status": solver.StatusName(status),
        "objective": solver.ObjectiveValue() if ok else None,
        "bound": solver.BestObjectiveBound(),
        "wall_s": round(wall, 1), "workers": workers,
    }
    grid = None
    if ok:
        grid = [[int(solver.Value(x[r, c])) for c in range(n)] for r in range(m)]
        out["independent_count"] = count_mono(grid, m, n)
    out["grid"] = grid
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("m", type=int)
    ap.add_argument("n", type=int)
    ap.add_argument("--model", choices=["count", "quad"], default="count")
    ap.add_argument("--time-limit", type=float, default=300.0)
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--lb", type=int, default=None,
                    help="proven lower bound from relax_lb.py")
    ap.add_argument("--json", type=str, default=None)
    args = ap.parse_args()

    res = solve(args.m, args.n, args.time_limit, args.workers, args.model,
                lb=args.lb)
    grid = res.pop("grid")
    print(json.dumps(res))
    if grid:
        for row in grid:
            print("".join("#" if v else "." for v in row))
    if args.json and grid:
        with open(args.json, "w") as f:
            json.dump({**res, "grid": grid}, f, indent=1)


if __name__ == "__main__":
    main()
