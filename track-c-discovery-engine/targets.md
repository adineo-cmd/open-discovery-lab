# Track C targets — scored queue (first harvest, 2026-11-09)

Scoring: **N** novelty (5 = no public doc/tool found), **F** feasibility
(5 = samples/files obtainable, simple structure), **V** value
(5 = preservation bodies / forensics / interoperability need it).
Total = N+F+V (max 15). Queue order by total.

## Harvested from (instruments)

- Just Solve the File Format Problem wiki (canonical unsolved-format
  registry; several pages have zero public documentation while dexvert ships
  samples).
- dexvert (Sembiance) — format identification corpus, samples referenced
  per format.
- awesome-rea / awesome lists — RE project space scan.
- Internet sweep (2026-11-09): fields where independents still make unique
  discoveries — bioacoustics (automated species monitoring, PMC11885706),
  taxonomy (new species descriptions), combinatorics/tilings (Works in
  Progress, Oct 2025), AI-safety math (arXiv:2609.15289, MAIS repo).

## Scored targets

| # | Target | Domain | N | F | V | Notes | Status |
|---|--------|--------|---|---|---|-------|--------|
| T-1 | WCN6750 wpss firmware anatomy (ELF headers, segment map, architecture ID) | Android blob RE | 5 | 5 | 5 | Upstream LibrePhone needs it; samples public (LineageOS); settles F-1 | → Track A |
| T-2 | Qualcomm Hexagon MDT/PIL image format — complete public spec | Android blob RE | 4 | 5 | 5 | Tooling exists upstream but no written spec anywhere | → Track A |
| T-3 | Reduq compressed format ("files start with 'r…'") | File format | 5 | 3 | 4 | JSIT page: format still being figured out; samples exist | ⬜ needs sample check |
| T-4 | Remedy Archive System format | File format | 5 | 3 | 4 | JSIT page has manual bit-manipulation decode hints only | ⬜ |
| T-5 | High-PM Gaia sources not in ultracool catalogs | Astronomy | 4 | 5 | 5 | Query running (q1); vetting decides | → Track B |
| T-6 | Undocumented legacy voice-recorder formats (queue from dexvert) | File format | 5 | 4 | 4 | Many devices, zero docs, samples in dexvert/samples | ⬜ enumerate top candidates |
| T-7 | FP6 TrustZone / keymaster / gatekeeper blob documentation | Android blob RE | 5 | 5 | 5 | Zero public docs; same image source as T-1 | → Track A queue |
| T-8 | FP6 fingerprint (goodix/fpc) firmware documentation | Android blob RE | 5 | 5 | 4 | Zero public docs | → Track A queue |
| T-9 | FP6 touchscreen controller firmware documentation | Android blob RE | 5 | 5 | 3 | Zero public docs | → Track A queue |
| T-10 | FP6 sensors (SLPI/sns) firmware documentation | Android blob RE | 5 | 5 | 4 | Zero public docs | → Track A queue |
| T-11 | Bioacoustics: open acoustic-monitoring dataset contributions | Ecology | 3 | 4 | 4 | Field open but needs hardware/recorders — deprioritized for this box | 💤 parked |
| T-12 | Combinatorics/tiling open problems (independent-discovery friendly) | Math | 4 | 3 | 4 | Viable per Works in Progress Oct 2025; needs deep specialist time | 💤 parked |
| T-13 | Min monochromatic rectangles in grid 2-colorings: a(9) of OEIS A399620, rows 9+ of A399621 | Math / combinatorial enumeration | 5 | 5 | 5 | OEIS entry 2026-09-05 tagged `more`; no paper/code computes a(9) (checked 2026-11-09). Track D adopted: T(9,3..6) certified, a(9) bracketed [74,80] | → Track D (kickoff done) |

## Method note

Novelty verified via GitHub code search + web search per target (dates in
journal). Feasibility verified only where noted; unchecked targets carry
optimistic defaults and get downgraded on evidence.
