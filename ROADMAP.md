# ROADMAP — future work and pending items

## Immediate (owner-gated)

| # | Action | Gate | Package location |
|---|--------|------|-----------------|
| 1 | **OEIS filing** — submit row 9 of A399621 (T(9,3..6)=3/6/16/24) + a(9) bounds (74≤a(9)≤80) to OEIS. URGENT: A399621 was edited 2026-11-11 — someone is active on the sequence. | Owner needs an OEIS account | open-research-lab math/grid-ramsey/results/oeis-submission-draft.md |
| 2 | **Codeberg PR filing** — 4 paste-ready PRs correcting upstream LibrePhone docs (AVR→RISC-V, WMI dispatch architecture, per-segment corrections, BT/boot-chain pointers). | Owner needs a Codeberg login | librephone-blob-research upstream-contribution/README.md + filing-checklist.md |
| 3 | **Qualcomm upstream PR-1 filing** — the AVR→RISC-V correction is the highest-priority single fix. | Same Codeberg login | librephone-blob-research qualcomm-fp6/upstream-pr-draft.md |

## Track A — MediaTek (next sessions)

| # | Task | Priority | Depends on |
|---|------|----------|-----------|
| M-1 | Close the MD32 decode gap — obtain an MD32 ELF (machine 0x2454) from another device/generation, or hand-build SLEIGH from the dense zone at 0x120000–0x160000 | HIGH — gates all md1dsp documentation | — |
| M-2 | Map the MIPS32 baseband (md1rom) — 1.3M instructions decoded, next: task identification, protocol documentation, dispatch architecture (same methodology as Qualcomm wpss) | HIGH — the largest MediaTek subsystem | M-1 not required (different core) |
| M-3 | Document the kernel-blob interface — what the Linux kernel sends each blob, what it expects back (the ath11k model applied to MediaTek) | HIGH — the clean-room input | M-1, M-2 |
| M-4 | HiFi3 audio DSP architecture (three-source evidence; no Xtensa decoder available) | MEDIUM | Xtensa capstone backend |
| M-5 | Camera CCU (ARCv2) — ARC EM4-FPU documentation depth | MEDIUM | ARC capstone backend or Synopsys docs |
| M-6 | Expand to other MTK generations (Dimensity MT6873+ has nanoMIPS per NCC/taszk — different from MT6785's MIPS32+MIPS16e) | MEDIUM | any Dimensity device with LineageOS |

## Track A — Qualcomm (follow-ons)

| # | Task | Priority | Depends on |
|---|------|----------|-----------|
| Q-1 | LPEC pulse-position refinement — FUN_1000c450 + FUN_1000b110 decompile, state+0xec/0xfc calibration constants | HIGH — upgrades the decoder from plausibility to reference quality | — |
| Q-2 | LPEC synthesis validation — Wine Rosetta (run PVoice.dll under Wine to produce reference PCM for diffing) | HIGH — closes the validation gap | Wine install |
| Q-3 | DiamondWare DWM bit-exact re-encode — the allocator release/tie-break tail (83 voice choices diverge past record 99) | MEDIUM — the grammar is confirmed complete; bit-exactness is polish | — |
| Q-4 | IGS .igm music grammar — the 0xC0–0xD0 control codes + f1/f3 flag semantics | MEDIUM | more .igm samples (discmaster lists ~46 IGS files) |
| Q-5 | NTitler BT30–BT80 variant documentation + bitmask→effect name mapping (NT.English locale) | MEDIUM | — |
| Q-6 | Qualcomm boot-chain deeper dive — uefi, abl, xbl_config internals (the container is mapped, the page body is partial) | MEDIUM | — |
| Q-7 | Cross-vendor comparison paper — the "unusual core for 3A" story (Qualcomm RISC-V ICP vs MediaTek ARCv2 CCU) as a formal research note | MEDIUM | both fronts at current depth |

## Track B — Astronomy (follow-ons)

| # | Task | Priority | Depends on |
|---|------|----------|-----------|
| B-1 | NIR J-band spectroscopy of the 29 promoted candidates (Feb–Apr 2027 window) — the physical step from candidate to discovery | HIGH — needs telescope time | — |
| B-2 | 2MASS/SDSS blink at epoch-2000 coordinates for the A-list | MEDIUM | SDSS SkyServer reachability |
| B-3 | Extend CatWISE/GCNS deep coverage beyond top-50 (IRSA ~13 s/query bottleneck) | MEDIUM | — |
| B-4 | Karpov 2025 (A&A 695, A195) cross-check — the 21,885-detection list as an independent exclusion set | MEDIUM | VizieR J/A+A/695/A195 reachability |

## Track D — Mathematics (follow-ons)

| # | Task | Priority | Depends on |
|---|------|----------|-----------|
| D-1 | Close the 3-color 11×11 gap (2 ≤ T₃(11,11) ≤ 10) — the joint two-sided relaxation is built; a better model is needed | HIGH — the frontier | — |
| D-2 | Extend 3-color bounds to (k,13+) sizes | MEDIUM | — |
| D-3 | Generalize the pipeline to c=4,5 colors | MEDIUM | — |
| D-4 | OEIS submission (see Immediate #1) | HIGH | OEIS account |

## Track C — Discovery engine (follow-ons)

| # | Task | Priority | Depends on |
|---|------|----------|-----------|
| C-1 | Complete the scored queue: R-3 Clarion record-body phase, R-5 rate arbitration, R-7 Sonic Arranger full decode, R-8 NTitler BT30–BT80 variants, R-10 ANSI Music .igm binary stream | MEDIUM | — |
| C-2 | dexvert contribution — submit the PVD decoder, IGS parser, and Clarion decoder to the dexvert project | MEDIUM | upstream contact |
| C-3 | Just Solve It wiki updates — document the decoded formats on the JSIT wiki | MEDIUM | JSIT reachability |

## Infrastructure (follow-ons)

| # | Task | Priority | Depends on |
|---|------|----------|-----------|
| I-1 | Hexagon decompiler — Ghidra decompiler timed out on big handlers; retry with longer timeout on idle box | MEDIUM | — |
| I-2 | Xtensa capstone backend — no decoder available for HiFi3 | MEDIUM | capstone upstream |
| I-3 | ARC capstone backend — no decoder available for CCU | LOW | capstone upstream |
| I-4 | MD32 SLEIGH — hand-build from the dense zone (the F-45 named lever) | HIGH — gates md1dsp | — |

## Standing rules (never forget)

From the owner's directives, institutionalized in AGENTS.md:

1. **RULE 0 — ABSOLUTE UNIQUENESS**: "Everything produced here must be
   unique — no one may have done it before. Never build anything that has
   already been built. Research it beforehand: search the whole internet
   FIRST." Adversarial audit every ~10 findings.
2. **RULE 1 — IMPROVE PREVIOUS WORK**: "If during any task you notice
   something in the lab's prior work that can be improved — fix it in the
   same session."
3. **RULE 2 — CROSS-VENDOR**: "Do all of LibrePhone's blobs" — Qualcomm
   AND MediaTek (and other vendors as targets emerge).
4. **RULE 3 — MEDIATEK OPEN-SOURCE PATH**: The lab is the clean-room SPEC
   producer for MediaTek proprietary blobs — ISA maps, protocol specs,
   format layouts that make open-source implementation possible.
5. **Fleet**: 2 agents concurrent, file-wall isolation, F-numbers at
   merge, silent-death detection.
6. **Exclusions**: CVE hunting, classical-cipher cryptanalysis.
7. **Everything reproducible**: every number regenerable from committed
   scripts; every claim carries a dated prior-art check.
