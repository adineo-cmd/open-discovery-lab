# FINDINGS — the running ledger

One line per finding. Status: `candidate` → `verified` (reproduced, evidence
linked) → `published` (writeup in papers/ or upstream PR merged).

| # | Date | Track | Finding | Status | Evidence |
|---|------|-------|---------|--------|----------|
| F-1 | 2026-11-09 | A | Upstream's claim that the WCN6750 wpss image contains an "8-bit AVR core, possibly RISCV32" is unverified in all public literature — no published analysis of the wpss ELF headers exists | verified (gap proven by literature search) | journal/2026-11-09.md |
| F-2 | 2026-11-09 | A | No free public documentation exists for Hexagon/qdsp6 firmware internals (SRLabs 2025 confirms; nothing since) | verified | [srlabs.de](https://srlabs.de/blog/hexagon-fuzz-full-system-emulated-fuzzing-of-qualcomm-basebands) |
| F-3 | 2026-11-09 | C | The Just Solve It wiki contains format pages with zero public documentation AND obtainable samples (dexvert) — a live queue of unique RE targets | verified | track-c-discovery-engine/targets.md |
| F-4 | 2026-11-09 | B | Backyard Worlds' 3,006 uncatalogued ultracool dwarfs (May 2026) proves uncatalogued-object mining in public data still yields named discoveries | verified | [phys.org](https://phys.org/news/2026-05-planet-volunteers-population-brown-dwarfs.html) |
| F-5 | 2026-11-09 | A | **The WCN6750 wpss core is 32-bit RISC-V** — `wpss.b07` is ELF32 EM_RISCV(243), entry 0x404000, version `WLAN.MSL.3.0.1-00591-QCAMSLSWPLZ-1`. Upstream's "8-bit AVR" guess is disproven; no public source documents this | verified | track-a-android-blobs/docs/fp6-architecture-census.md |
| F-6 | 2026-11-09 | A | **FP6 camera ICP + all VPU firmware are RISC-V** (e_machine=94, historic RISC-V ID): `CAMERA_ICP.*` (`CICP.FW.7.0-00021`, Mimas/Skye platforms), `vpu20/30/33_*.mbn`. First public ISA identification for these cores | verified | track-a-android-blobs/docs/fp6-architecture-census.md |
| F-7 | 2026-11-09 | A | **Qualcomm .bXX per-segment ELF headers carry junk e_machine values** (0 on 166 files, 1 on dtb files, even x86=3 on wpss.b08, a data segment at vaddr 0x4ff00000). Architecture ID must use .mdt headers + entry sanity, not segment headers | verified | track-a-android-blobs/docs/fp6-architecture-census.md |
