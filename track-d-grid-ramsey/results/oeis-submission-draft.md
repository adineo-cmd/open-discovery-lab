# OEIS submission package — A399620 / A399621 (row 9)

Status: **drafted, ready to file** once the submitter has an OEIS account
(filing requires one; https://oeis.org/wiki/Welcome). a(9) section marked
PENDING-T74 — finalize after the running CP-SAT completes (SAT → a(9)=74
exact; INFEASIBLE → LB=75). Everything else is final and certified.

## What we're contributing

- **A399621** (T(k,n) = min monochromatic rectangles over 2-colorings of
  k×n grid): **new row-9 values T(9,3)=3, T(9,4)=6, T(9,5)=16, T(9,6)=24**
  — each CP-SAT-proven OPTIMAL with objective equal to a proven exact
  aggregation-relaxation lower bound, and each witness grid re-counted by an
  independent pure-Python counter. Certificates:
  `track-d-grid-ramsey/results/t93.json … t96.json`.
- **A399620** (a(n) = T(n,n)): **first bounds for the open a(9): 74 ≤ a(9) ≤ 80**
  (PENDING-T74: may become a(9)=74 exact, or 75 ≤ a(9) ≤ 80), plus LB(10,10)=130.

## Proposed A399621 edit (sequence edit form)

```
%e A399621 Row 9: T(9,3)=3, T(9,4)=6, T(9,5)=16, T(9,6)=24. Also T(9,7) is
between 39 and 42 and T(9,8) between 52 and 56 (2026).
%e A399621 Witness grids and machine-checkable certificates:
https://github.com/adineo-cmd/open-discovery-lab/tree/main/track-d-grid-ramsey/results
```

## Proposed A399620 edit (sequence edit form)

```
%e A399620 74 <= a(9) <= 80 [PENDING-T74 — update per outcome]. LB(10,10)=130
(2026). The lower bound is an exact aggregation relaxation: for any 2-coloring,
the number of monochromatic rectangles is at least min over per-row-pair
agreement-count profiles of Sum_{i<j} [C(a00_ij,2)+C(a11_ij,2)], subject to
column-count identities; solved exactly with CP-SAT. The bound is tight at
n=6,7,8 (6, 21, 40).
%e A399620 a(9) >= 74 proof + 80-rectangle witness grid:
https://github.com/adineo-cmd/open-discovery-lab/tree/main/track-d-grid-ramsey/results
```

## Suggested comment (both sequences)

```
%C Computed 2026-11-09/10 by the Open Discovery Lab
(https://github.com/adineo-cmd/open-discovery-lab): exact aggregation-relaxation
lower bounds + CP-SAT construction search with per-row-pair count variables and
symmetry breaking; every witness independently re-counted.
```

## Filing checklist

- [ ] OEIS account for the submitter (or the lab owner)
- [ ] Finalize a(9) line after T74 (see above)
- [ ] Attach/reference witness JSONs (t93–t96, sq9) — offer as links, not uploads
- [ ] Credit: solver stack (OR-Tools CP-SAT); method documented in
      track-d-grid-ramsey/README.md
- [ ] After acceptance: set FINDINGS.md F-10/F-12 status → `published`

## Note on scope

Row 9 submission covers only values we can PROVE. T(9,7)/T(9,8) brackets
(39–42, 52–56) are stated as bounds, not values. No unverified claims.
