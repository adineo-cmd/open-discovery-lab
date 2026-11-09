# Track D — Grid Ramsey Minima (combinatorial enumeration)

**Mission.** Extend the OEIS tables of *minimum number of monochromatic
rectangles* in 2-colorings of grids — **A399620** (n×n) and **A399621**
(k×n triangle) — with certified new terms, using an exact CP-SAT pipeline
this lab developed: a proven aggregation lower bound composed with a
construction search.

## The verified gap (prior-art check, 2026-11-09)

- OEIS [A399620](https://oeis.org/A399620): minimum #monochromatic
  axis-parallel rectangles (4 corners same color) in any 2-coloring of an
  n×n grid. Known only for n=1..8 (a(8)=40). Authored by Jeremy F. Alm,
  **2026-09-05**, keywords `nonn,hard,more` — the OEIS itself asks for
  more terms. No b-file values beyond row 8 (36 triangle terms in A399621).
- OEIS [A399621](https://oeis.org/A399621): same minimum for k×n grids,
  rows n=1..8 only. Same author/date.
- Web search (2026-11-09): no paper or preprint computes a(9) or row 9.
  Closest prior art: MIP for monochromatic *squares* (2015,
  academia.edu/53523167), Fenner–Gasarch rectangle-free grid coloring
  program, "Monochromatic Boxes in Colored Grids" (arXiv:0810.3019,
  defines (c,t)-guaranteed grids), Dumitru arXiv:2512.23303 (Dec 2025,
  rectangle-free colorings). None gives minimization values past 8.
- GitHub code search `"monochromatic rectangles" language:Python`
  (2026-11-09): no public minimization solver exists (only unrelated
  procgen/ARC hits). Verified gap.

## Method (exact, reproducible)

Two-stage proof composition (both stages exact):

1. **Aggregation lower bound** (`tools/relax_lb.py`). Exact identities:
   `mono = Σ_{row pairs} [C(a00,2)+C(a11,2)]`,
   `Σ a00 = Σ_c C(z_c,2)`, `Σ a11 = Σ_c C(m−z_c,2)` (z_c = zeros in
   column c). Solve the aggregation relaxation to proven optimality with
   CP-SAT → LB(m,n). Valid because it drops only realizability of the
   per-pair pattern. **Validation: LB = 6, 21, 40 for n=6,7,8 — exactly
   the OEIS values (tight).** LB(9,9)=74; LB(10,10)=130; LBs for the
   rectangular table computed for all k×9.
2. **Construction search** (`tools/min_mono_rect.py`, count model v2).
   CP-SAT over cells with per-row-pair count variables (exact
   linearization C(a,2)=Σ_{k≤a}(k−1)), symmetry breaking x[0][0]=0 +
   row-lex order, LB added as constraint. `OPTIMAL` with objective = LB
   certifies the value; every witness grid is re-counted by an
   independent pure-Python counter.

## Results (2026-11-09/10)

See `results/a399620_a399621.md` for the full table, witness grids and
solver stats. Headline:

- **a(9) first bounds 74 ≤ a(9) ≤ 80** (9×9): a(9) of A399620 was
  completely unknown; LB proven by exact aggregation relaxation, UB by
  verified CP-SAT witness.
- **Four new exact values** in row 9 of A399621: T(9,3)=3, T(9,4)=6,
  T(9,5)=16, T(9,6)=24 (OPTIMAL, objective = proven LB).
- Partial brackets: T(9,7)∈[39,42], T(9,8)∈[52,56].
- Pipeline validated: reproduces known a(5..8) = 2, 6, 21, 40; the
  relaxation bound is exactly tight at n=6,7,8.

## Negative / partial results

- Naive per-rectangle CP-SAT model (v1, `--model quad`): proves 5×5, 6×6
  optimal (0.1 s / 49 s) but **stalls on proofs from 7×7 up** (300 s:
  objective 21 found, bound only 8). Documented so nobody repeats it.
- 7×7 with count model v2: finds 21 fast, proof still stalls without the
  analytic LB (180 s: bound 13). The LB constraint is what makes the
  certification tractable.
- 12-proc simulated annealing (`tools/sa_search.py`, 100 s): best
  verified 104 on 9×9 — not competitive with CP-SAT's 80. Abandoned.
- 9×9 gap 74→80 not closed this session (construction side is the
  bottleneck). Closing it is one command once any 74-rectangle coloring
  is found: `python3 tools/min_mono_rect.py 9 9 --lb 74`.

## Next steps

1. Close a(9): construction search at 74 (local search guided by
   agreement-count structure, or long CP-SAT runs); then T(9,7)/T(9,8).
2. Submit a(9), T(9,k) row and any further certified cells to OEIS
   A399620/A399621 (style: new row + comment with witness grid).
3. Push to 10×10 (LB(10,10)=130 known from relax_lb).
4. 3+ colors: c-coloring analogues (the (c,t)-guaranteed literature) —
   same pipeline, objective counts rectangles of each color.
