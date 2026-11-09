# a(9) attack — session log (2026-11-10)

**Target:** OEIS A399620 a(9) = minimum #monochromatic rectangles in a
2-coloring of the 9×9 grid.  Verified state at session start
(F-10): **74 ≤ a(9) ≤ 80**.  A 74-witness closes it; any UB below 80 or
any LB above 74 improves the published bracket.

## Baseline reproduction (passed)

- Existing witness `results/sq9.json` re-counted by a fresh independent
  pure-Python corner counter (written for this session, not the lab's):
  **80** — matches the solver objective.  Pair-profile of the witness:
  20 pairs (agree=4, a00=2, a11=2, mono 2), 8×(3, (1,2)/(2,1), mono 1),
  8×(5, (2,3)/(3,2), mono 4); row weights 4..5, column weights 4..5.
- `tools/relax_lb.py 9 9` re-run: **LB = 74, OPTIMAL, 0.1 s.**

## Relaxation optimum profile (new analysis)

Solved the aggregation relaxation and extracted its optimal per-row-pair
counts (any 74-rectangle coloring must project onto an optimal
relaxation profile):

> 32 of 36 row pairs at (a00,a11) = (2,2)  [agree in 4 cols]
> 2 pairs at (2,3)  [agree 5], 2 pairs at (1,2)  [agree 3]
> column zero-counts: five 4s and four 5s.

**Rigidity note:** a 74-coloring needs near-simplex row structure — 9
binary rows with 32/36 pairs agreeing in exactly 4 columns with a (2,2)
split.  One natural construction route fails outright: take a punctured
Hadamard-12 simplex (rows pairwise agree 5 in 11 columns) and delete 2
columns; the deleted columns classify the 9 rows into 4 types, and
pigeonhole (9 rows, 4 types) forces ≥ 6 pairs agreeing in *both* deleted
columns, but the profile allows only 2 (the (2,3) pairs).  So the
simplex-with-deletions family cannot realize the profile; whether *any*
grid can is exactly the T74 feasibility question below.

## Method 1 — iterated local search (new tool `results/ls_a9.py`)

Incremental state: per-row-pair (a00, a11) and mono counts; exact
O(1)-per-pair deltas for **cell flips**, **whole-row flips**, **whole-column
flips**; steepest descent + bounded plateau drift, then kicks (cell-flip
bursts, row/col flips, 2-3 row re-randomizations); periodic restarts.
Every claimed best re-counted by the independent counter before being
recorded.  Self-test: 300 random mixed moves + 200 delta/apply
comparisons all consistent with the counter.

**Local-structure findings (negative for UB improvement):** the 80-witness
is a strict local optimum against
- all single-cell flips (best delta 0 — flat, none negative),
- all whole-row and whole-column flips (best delta +7),
- all 2-flips within a row or within a column (best delta 0),
- all 3-flips within a row or within a column (best delta 0).

ILS runs (3 processes × ~30 min, killed at session end; no process broke
below 80 at any point):
| start | first descent | best after session |
|---|---|---|
| 80-witness | 80 | **80** |
| SA 104-witness (`results/sa9.json`) | 80 (it 1) | **80** |
| random balanced | 82→80 | **80** |

The landscape funnels to 80 from every direction; no process broke below
80.  Witnesses: `results/certificates/a9_ils_ub80_seed22.json` (re-derived
80 from the 104 start — independently re-counted).

## Method 2 — CP-SAT target runs (`results/cpsat_a9_ub.py`)

Count model v2 (same formulation as `tools/min_mono_rect.py`) + hard
`obj ≤ target` cap + witness hint + per-improvement callback (each
incumbent re-counted independently).  ortools 9.15 / protobuf 6.33;
note `AddHint` takes one (var, value) pair per call in this API (the
list form of the older API throws).

| run | config | time | outcome |
|---|---|---|---|
| A | minimize, hint = 80-witness, lb 74, 6 workers | ~15 min (killed) | **no improvement past 80** (killed) |
| B | hard cap `obj ≤ 79`, hint = 80-witness, 3 workers | ~15 min (killed) | no feasible ≤ 79 found (killed; UNKNOWN) |
| T74 | hard cap `obj ≤ 74` (⇒ = 74 given LB), 12 workers | ~14 min (killed at budget) | **no obj-74 witness in ~870 s × 12 workers** (callback would report instantly); UNKNOWN — session budget expired before infeasibility could be settled |

## Outcome (honest negatives)

**The bracket 74 ≤ a(9) ≤ 80 stands; no bound moved this session.**  What
was established:

1. **80 is a strong attractor.**  Every search method converged to or was
   pinned at 80: three independent ILS starts (including the weak SA-104
   start, which dropped to 80 in one descent), CP-SAT minimize-from-hint,
   and the profile analysis all agree.  The witness is locally optimal
   against every flip neighborhood tried (1-, 2-, 3-flips within
   rows/columns, whole rows, whole columns) — first non-flat moves
   require structurally larger rearrangements.
2. **74 is heavily constrained (new analysis).**  Any 74-coloring must
   project onto the relaxation profile 32×(2,2) + 2×(2,3) + 2×(1,2) with
   column zero-counts {4,4,4,4,4,5,5,5,5}; the punctured-simplex
   construction family provably cannot realize it (pigeonhole: 9 rows in
   4 deletion-classes force ≥ 6 pairs agreeing in both deleted columns,
   the profile allows 2).  Finding *any* 74-witness, if one exists,
   requires leaving this family.
3. **Negative run records** (per lab principle 3): runs A, B, T74 above;
   the T74 run is the natural next session target — give it the full
   1450 s+ budget (or days) since an INFEASIBLE there raises the LB to
   75, and a SAT there closes a(9) = 74 exactly.

**Recommended next attack** (out of scope for this session's budget):
rerun T74 to completion (hours); if SAT → closure.  If it stalls, try
the profile-guided feasibility model: pin each row pair's (a00, a11) to
an optimal-profile multiset (32 pairs (2,2), 2 (2,3), 2 (1,2)) — a much
smaller satisfaction problem whose UNSAT (over all profile assignments)
would prove LB ≥ 75 combinatorially.

## Reproduce

```bash
python3 tools/relax_lb.py 9 9                                   # LB 74
python3 results/cpsat_a9_ub.py --hint results/sq9.json \
        --lb 74 --time-limit 1800 --workers 12 --seed 1 --out /tmp/inc.json
python3 results/ls_a9.py 11 <epoch-deadline> results/sq9.json /tmp/ls.json mix
python3 results/cpsat_a9_ub.py --hint results/sq9.json --lb 74 \
        --ub-target 74 --time-limit 1450 --workers 12 --seed 5 --out /tmp/t74.json
```
