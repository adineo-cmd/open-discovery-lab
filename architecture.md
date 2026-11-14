# Architecture — Open Discovery Lab

## Repos
- open-discovery-lab (umbrella: FINDINGS.md ledger F-1..F-49, journals, discovery engine, prior-art audit)
- librephone-blob-research (Track A body: qualcomm-fp6/ + mediatek/ + papers/ + upstream-contribution/)
- open-research-lab (math/grid-ramsey + astronomy/high-pm-survey + discovery-engine)

## Data flow
1. Fleet agents (max 2 concurrent) research assigned tracks → push only their own directories
2. Lead merges ledger rows (F-numbers monotonic), journals, README updates
3. Standing rules in AGENTS.md (Rule 0 uniqueness, Rule 1 improve) + memory directives
4. Ledger sync agents push local→umbrella byte-verified (fetch-back + sha256)

## Key infrastructure
- Ghidra 12.2 + JDK 25 (Hexagon + x86 + MD32 decode; setup in hexagon-decode.md)
- payload_dump.py / extract_vfat.py / census.py (OTA → partitions → blob census)
- Gaia aip.de TAP chunked harvest + IRSA/SIMBAD-CFA vetting pipeline
- CP-SAT solver stack (2-color + 3-color grid Ramsey certificates)

## Conventions
- F-numbering monotonic at merge; agents propose "F-N-or-next-free"
- File-wall isolation per agent; byte-verified pushes (fetch-back + sha256)
- Ledger sync agents handle FINDINGS/journal pushes (local authoritative, remote-only preserved)
