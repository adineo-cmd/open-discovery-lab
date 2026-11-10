# Open Discovery Lab

Original research, recorded openly. The goal is **not** to re-implement things
that already exist — every track targets a *verified gap*: something the
relevant community needs, that nobody has published yet.

> **2026-11-10: the lab split by owner directive.** The two specialized
> repos now carry the bodies of work; this repo remains the chronological
> lab notebook (findings ledger F-1..F-15, journals, discovery engine).
>
> - 🔧 Android blob RE (Qualcomm FP6 + MediaTek) →
>   [adineo-cmd/librephone-blob-research](https://github.com/adineo-cmd/librephone-blob-research)
> - 📐 Mathematics + astronomy + discovery engine →
>   [adineo-cmd/open-research-lab](https://github.com/adineo-cmd/open-research-lab)

## Findings ledger (F-1..F-15, all verified)

| # | Track | One-line finding |
|---|-------|------------------|
| F-5 | A | WCN6750 wpss core = 32-bit RISC-V (instruction-level proof) |
| F-6 | A | Camera ICP + VPU firmware = RISC-V (first public ISA ID) |
| F-7 | A | Qualcomm .bXX segment headers carry junk e_machine values |
| F-8 | A | wpss runs Qualcomm QURT RTOS on RISC-V |
| F-9 | A | First ath11k↔WCN6750 WMI constant cross-reference |
| F-10 | D | Four new exact OEIS values (row 9, A399621) + first a(9) bounds |
| F-11 | B | Full-sky Gaia DR3 high-PM harvest: 130,318 sources |
| F-12 | D | a(9) attack: negative result + structural evidence (80 = attractor) |
| F-13 | B | Epoch-aware vetting: 621 uncatalogued candidates (39 conf-A) |
| F-14 | A | First public BT + TrustZone firmware censuses (FP6) |
| F-15 | A | First public boot-chain census; housekeeping cores = RISC-V |

Full evidence rows: [`FINDINGS.md`](FINDINGS.md). Dated journals:
[`journal/`](journal/). Owner directives: [`SCOPE.md`](SCOPE.md).

## Principles

1. **Facts, not blobs.** No proprietary binary content is ever committed.
2. **Clean-room discipline.** 3. **Negative results are results.**
4. **Everything reproducible.** 5. **Contribute upstream.**

## License

MIT for code. Documentation and findings: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
