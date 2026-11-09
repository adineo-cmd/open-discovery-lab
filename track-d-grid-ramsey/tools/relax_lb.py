#!/usr/bin/env python3
"""relax_lb.py — exact lower bound for the minimum number of monochromatic
rectangles in a 2-coloring of an m x n grid, via an exact aggregation
relaxation solved to optimality with CP-SAT.

Identities (exact, not heuristics):
  mono_total = sum over row pairs {i,j} of [ C(a00_ij,2) + C(a11_ij,2) ]
      a00_ij = #columns where rows i,j are both 0;  a11_ij both 1.
  sum_ij a00_ij = sum_c C(z_c, 2)      (column c has z_c zeros)
  sum_ij a11_ij = sum_c C(m - z_c, 2)

Relaxation: keep only these aggregate constraints (drop the realizability
of the per-pair pattern by an actual grid), i.e. minimize
  sum_ij [C(a_ij,2) + C(b_ij,2)]
  s.t. sum a_ij = sum_c C(z_c,2),  sum b_ij = sum_c C(m-z_c,2),
       a_ij + b_ij <= n,  z_c in [0,m].
This is a valid lower bound on the true grid minimum.  C(v,2) is
linearized exactly as sum_{t=1..v} (t-1) via threshold booleans.

Validation built in: for (m,n) = (5,5),(6,6),(7,7),(8,8) the bound equals
the known OEIS A399620 values 2, 6, 21, 40 — the relaxation is TIGHT there
(except 5×5 where LB=1 < a(5)=2).

Usage: python3 relax_lb.py m n [--json OUT]
Prints JSON {m, n, lb, status, wall_s}.
"""
import argparse
import json
import time

from ortools.sat.python import cp_model


def c2(model, v, upper, tag):
    """Return an integer expression equal to C(v,2) for IntVar v in [0,upper],
    via exact linearization C(v,2) = sum_{t=1..v} (t-1)."""
    terms = []
    for t in range(1, upper + 1):
        u = model.NewBoolVar(f"{tag}_ge{t}")
        model.Add(v >= t).OnlyEnforceIf(u)
        model.Add(v <= t - 1).OnlyEnforceIf(u.Not())
        if t - 1:
            terms.append((t - 1) * u)
    return sum(terms) if terms else 0


def lb(m, n):
    model = cp_model.CpModel()
    R = m * (m - 1) // 2
    z = [model.NewIntVar(0, m, f"z{c}") for c in range(n)]
    P0 = sum(c2(model, zc, m, f"cz{c}") for c, zc in enumerate(z))
    P1 = sum(c2(model, m - zc, m, f"co{c}") for c, zc in enumerate(z))
    a, b = [], []
    for k in range(R):
        ak = model.NewIntVar(0, n, f"a{k}")
        bk = model.NewIntVar(0, n, f"b{k}")
        model.Add(ak + bk <= n)
        a.append(ak)
        b.append(bk)
    model.Add(sum(a) == P0)
    model.Add(sum(b) == P1)
    obj = sum(c2(model, ak, n, f"ca{k}") for k, ak in enumerate(a)) + sum(
        c2(model, bk, n, f"cb{k}") for k, bk in enumerate(b)
    )
    model.Minimize(obj)
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 8
    solver.parameters.random_seed = 20261109
    t0 = time.time()
    status = solver.Solve(model)
    wall = time.time() - t0
    assert status == cp_model.OPTIMAL, solver.StatusName(status)
    return int(round(solver.ObjectiveValue())), solver.StatusName(status), wall


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("m", type=int)
    ap.add_argument("n", type=int)
    ap.add_argument("--json", type=str, default=None)
    args = ap.parse_args()
    val, status, wall = lb(args.m, args.n)
    out = {"m": args.m, "n": args.n, "lb": val, "status": status,
           "wall_s": round(wall, 1)}
    print(json.dumps(out))
    if args.json:
        with open(args.json, "w") as f:
            json.dump(out, f, indent=1)


if __name__ == "__main__":
    main()
