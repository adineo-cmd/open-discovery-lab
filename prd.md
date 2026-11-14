# Product Requirements Document — Open Discovery Lab

## Overview
- Project: Open Discovery Lab (3 repos: umbrella + librephone-blob-research + open-research-lab)
- Objective: produce verified-original research (no prior art) across reverse engineering, mathematics, and public-data science — everything recorded openly with reproducible evidence
- Scope: Android firmware RE (Qualcomm + MediaTek), legacy file-format RE, grid Ramsey mathematics, Gaia-based astronomy, discovery engine. Out of scope: CVE hunting, cipher cryptanalysis (owner exclusions)

## Requirements
1. Every finding passes the Rule-0 uniqueness gate (whole-internet prior-art search, dated, recorded)
2. Every finding ships reproducible scripts + evidence (no unverifiable claims)
3. No proprietary binary content in git (facts and derived data only)
4. Two research agents run concurrently at all times (fleet rule)
5. Adversarial prior-art audit every ~10 findings or per session
6. Findings improve previous work when opportunities appear (Rule 1)

## Constraints
- Account cap: 2 concurrent agents
- Network: CDS/Strasbourg + some mirrors unreachable; gh aircrane absent; large downloads flaky
- Machine sleeps kill detached processes and agent contexts (recovery pattern established)
- Policy: TZ/DRM census-only; Sony codec RE = interoperability purpose, derived facts only

## Acceptance Criteria
- Ledger rows: `verified` status only with evidence links + commit SHAs
- Prior-art audit verdicts recorded per finding (results/prior-art-audit.md)
- Corrections applied in place where claims fail (F-9 precedent)
