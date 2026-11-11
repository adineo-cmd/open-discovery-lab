# Prior-Art Audit of FINDINGS.md (F-1..F-26) — independent re-verification

**Auditor:** independent prior-art audit agent (Open Discovery Lab), 2026-11-11.
**Mandate:** adversarially re-verify every finding's uniqueness claim against public
sources; flag anything NOT unique. Corrections are applied by the lead from this
report only; nothing else in the repo was modified by this audit.

**Sources used:** GitHub code search (REST, repo-independent; adineo-cmd results
excluded from adjudication), WebSearch (general web, distro/linux-firmware listings,
arXiv/A&A), direct fetches of oeis.org, librephone.fsf.org, GitHub repos/commits.
**Audit date:** 2026-11-11 (all verdicts as of this date).

## Verdict summary

| Verdict | Findings |
|---|---|
| UNIQUE-CONFIRMED | F-3, F-4, F-8, F-9, F-10, F-11, F-12, F-13, F-14, F-17, F-19, F-20, F-21, F-22, F-23, F-24, F-25, F-26 |
| OVERLAP-FOUND (partial; core novelty survives with rewording) | F-5, F-6, F-7 |
| CORRECTION-NEEDED | F-1, F-2, F-15, F-16, F-18 |

**Single most important result:** the FSF **LibrePhone** project
(github.com/fabiorafaelcoutada/librephone, author Rob Savoye rob@fsf.org,
docs committed 2026-01-16; mirrored at librephone.fsf.org) **publicly analyzes the
wpss.bXX ELF segments file-by-file** — including a hedged RISCV32 identification of
wpss.b07 and an i386 misidentification of wpss.b08 — ten months before the lab's
work. F-1/F-5/F-7 as written are too strong. Separately, **gdrci/Research** (commit
58d764f, 2026-10-08) publishes raw `e_machine` header dumps for CAMERA_ICP / vpu20 /
evass (labeled EM_XTENSA = numeric 94), one month before F-6.

## Key prior-art discoveries (detail)

### P1. LibrePhone (FSF) — wpss per-file docs (predates lab by ~10 months)
- Repo: github.com/fabiorafaelcoutada/librephone, `docs/wpss.b07.md` created
  2026-01-16T19:16Z ("Initial minimal draft", Rob Savoye). Site: librephone.fsf.org/site/wireless.
- Exact quotes: "This file seems to be a RISCV32, several tools identify it as such...
  The objdump program does dissasemble it... Some of the generated code looks like
  good RISCV assembly, but it has blocks that look like total garbage."; index:
  "wpss.b07 - ELF32 little endian RISCV32 binary ?", "wpss.b08 - ELF32 little endian
  Intel i386 binary", "wpss.b09 - data file, unknown architecture", "wpss.b10 - data
  file of error messages", "wpss.b12 - 3 certificates in DER format (x509 v3)".
- Wireless page: "This chip appears to have an embedded 8 bit ATMel AVR core, and
  possibly a RISCV32 core as well" (this is the "upstream claim" F-1 refers to);
  "It looks like it also contains a RISCV core. The blob that seems to be an Intel
  x86_32 is suspicious."; WPSS "presents a fake PCI device" (transport framing).
- ath11k page (content referencing email 2026-06-21): full HDD/WMA/WMI/HTT/HTC/HIF
  layering, "most WPSS blob files are data files (calibration tables, RF
  configuration, certificates), not executables", fake-PCI note.
- What LibrePhone did NOT do: no e_machine/entry-point analysis, no instruction-level
  proof, no WMI constant xref into the blob, no b09 registry discovery ("wpss.b09 ...
  data file ... file thinks this a Sony PlayStation PSX image"), b06 left "unknown
  architecture".

### P2. gdrci/Research — peripheral firmware header dump (2026-10-08)
- `data/userspace/peripheral_firmware_headers.txt`, commit 58d764f (2026-10-08T17:07Z):
  "CAMERA_ICP.mdt: size 7724, e_machine EM_XTENSA, e_entry 0x0, program headers 21...
  vpu20_4v.mbn: size 2079528, e_machine EM_XTENSA, e_entry 0xf500000... evass.mbn..."
  plus WPSS/BT firmware images and "build IDs from the modem verinfo manifest" for a
  same-generation platform. Raw e_machine=94 values are public (as EM_XTENSA label);
  the historic-RISC-V interpretation and ISA tie-in remain the lab's.

### P3. Hexagon documentation is now freely available (F-2)
- docs.qualcomm.com hosts Hexagon Programmer's Reference Manuals free of charge:
  V73 (80-N2040-53, Jan 2024), V75/V75 HVX (mirrors), V79 (80-N2040-60); V5/V6x/V66
  manuals circulate publicly; QEMU and LLVM implement Hexagon openly; IDA Hexagon
  modules (fevv9/gsmk_hexagon); Black Hat Asia 2025 QDSP6 ISDB/JTAG paper.
- Leaked Hexagon build trees on GitHub (Rivko/android-firmware-qti-sdm670,
  David112x/android-firmware-qti-sdm660, arzekrasr/MPSS.HA.1.1,
  robcore/flybirdlaboratory_adsp_proc) expose QURT kernel internals (QURTK_*,
  UTCB, crashman/cmm scripts, qurt_consts.py) and qualcomm/hexagon-hypervisor
  publishes qurt includes.

### P4. OEIS state for Track D (as of 2026-11-11)
- A399621 (Jeremy F. Alm, Sep 05 2026): rows n=1..8 only; last row
  "0, 0, 2, 4, 12, 18, 30, 40"; no T(9,k) values; no 3-color variant; crossref only
  "Main diagonal is A399620". Page footer: "Last modified November 11 11:31 EST 2026"
  (edited today — edit history not retrievable this session; re-verify before/after
  any lab submission).
- A399620: 8 terms "0, 0, 0, 0, 2, 6, 21, 40", keywords nonn,hard,more; a(9) unknown;
  no bounds (74..80) and no a(10)>=130 anywhere on the page.
- No OEIS or academic source found publishing T(9,3..6)=3/6/16/24, the 74<=a(9)<=80
  bracket, LB(10,10)=130, or any 3-color minimum-count values. Adjacent but
  non-overlapping literature: Fenner/Gasarch et al. (rectangle-free grids, G_3=11),
  Liu SOCS 2021 (shift patterns), Dumitru et al. arXiv:2512.23303 (Dec 2025,
  Gallai variations), Axenovich et al. INTEGERS 2008.

### P5. Astro method overlap (F-13/F-21/F-25, methodology level)
- Karpov 2025, A&A 52011 (March 2025), "New ultracool dwarf candidates from
  multi-epoch WISE data": publishes uncatalogued high-PM ultracool-dwarf candidates
  from WISE epochs (below Gaia's limit). Same hunt at methodology level, different
  data regime; the lab's Gaia-anchored cohort and 29-object package remain
  unpublished. Backyard Worlds (already cited as F-4) is the citizen-science analog.

### P6. XBL container structure is public (F-15)
- linux-msm/xbltools (`unpackxbl`): "uses brute-force and heuristics to split a
  Qualcomm XBL partition image" into sbl1.elf + xbl_core.elf + xbl_sec.mbn; coreboot
  createxbl.py builds such containers. Generic 3-component XBL container is public
  prior art; FP6-specific 3-ELF census (junk wrapper + RV32 + AArch64) is not.
- "Milos" SoC name is public (linux-wireless ath11k list, Jan 2026, "ath11k WiFi
  bringup on Milos SoC"); deriving it from FP6 xbl_config DTBs is the lab's increment.

### P7. MTK header/GFH public fragments (F-16/F-18)
- Magisk documents `struct mtk_hdr` with magic 0x58881688 (boot-image MTK header).
- mtkclient (bkerler) publishes GFH structure definitions; MediaTek GFH record
  format partially public.
- Mainline kernel docs (drivers/remoteproc/mtk_scp) describe MTK SCP as a
  Cortex-M4-based microcontroller — Cortex-M4 + small RTOS for MTK companion cores
  is public knowledge, so F-16's "first" must be scoped to the Helio G95 tinysys
  blobs at instruction level.
- zrax's "socboot2" (cited by F-18) could not be located publicly this session
  (search: `zrax socboot2 mtk_hdr MediaTek bootloader format GitHub` — no repo found);
  the citation risks being a dangling reference; verify or replace.

## Per-finding audit table

| F-# | Queries run (exact strings) | Sources checked | Verdict | Evidence / remaining uniqueness |
|---|---|---|---|---|
| F-1 | web: `WCN6750 wpss firmware RISC-V`; `Qualcomm wpss "8-core" AVR RISCV32 firmware`; `wpss.b07 OR wpss.mdt ELF header analysis Qualcomm`; code: `wpss.b07` | librephone.fsf.org (site/wireless), fabiorafaelcoutada/librephone docs, distro linux-firmware listings, ath11k list | **CORRECTION-NEEDED** | "No published analysis of the wpss ELF headers exists" is false: LibrePhone's per-file wpss.bXX docs (2026-01-16) are published ELF-header-level analysis. Correct claim: no *independent instruction-level* analysis exists; upstream's own tool-based identifications are hedged ("?", file-magic level). |
| F-2 | web: `Hexagon qdsp6 programmer reference manual free public documentation` | docs.qualcomm.com PRMs, QEMU/LLVM, IDA modules, Black Hat Asia 2025, leaked build trees | **CORRECTION-NEEDED** | Free Hexagon ISA docs exist (PRM V73 Jan 2024 / V75 / V79 on docs.qualcomm.com; QEMU, LLVM). Narrow the gap to *firmware-image internals* (image format, QURT structure, wpss/wlan firmware layout), which SRLabs-style statements actually cover. |
| F-3 | (methodology claim; dexvert/JSI treated as input, not competitor) | web | **UNIQUE-CONFIRMED** (low-depth check) | No competing published "zero-doc + obtainable-sample" RE target queue found. |
| F-4 | (citation finding) | phys.org link | **UNIQUE-CONFIRMED** (informational) | Article exists; no correction. |
| F-5 | same as F-1 + code: `QURTK UTCB`; `dog_hal_moselle` | LibrePhone wpss.b07.md (2026-01-16), wireless.md | **OVERLAP-FOUND (partial)** | RISCV32 identity of wpss.b07 is public (hedged, tool-level) since 2026-01-16. Still unique: instruction-level RV32 machine-mode startup (csrs mstatus/csrw mtvec), entry 0x404000, WLAN.MSL.3.0.1-00591 tie-in, definitive AVR-guess disproof. Drop "no public source documents this". |
| F-6 | code: `CAMERA_ICP e_machine`; `CAMERA_ICP RISCV firmware` | gdrci/Research peripheral_firmware_headers.txt (commit 58d764f, 2026-10-08) | **OVERLAP-FOUND (partial)** | Raw e_machine=94 for CAMERA_ICP/vpu20/evass published 2026-10-08 (labeled EM_XTENSA). Still unique: the historic-RISC-V interpretation, CICP.FW.7.0-00021/Mimas-Skye mapping, vpu20/30/33 family sweep. Qualify "first public ISA identification" -> "first correct-ISA interpretation + family census". |
| F-7 | same as F-1 | LibrePhone wireless.md ("wpss.b08 - ... Intel i386 binary"; "the various programs sometimes disagree") | **OVERLAP-FOUND (partial)** | i386 junk-e_machine observation on wpss.b08 is public (Jan 2026). Still unique: systematic 166-file sweep (e_machine=0 pattern, dtb=1), .mdt+entry-sanity methodology prescription. |
| F-8 | web: `"QURT" WiFi firmware wpss OR wcn6750 OR ath11k strings`; code: `QURTK UTCB`, `dog_hal_moselle` | leaked SDM670/MPSS trees, qualcomm/hexagon-hypervisor, LibrePhone wireless/ath11k pages | **UNIQUE-CONFIRMED** | No public source says wpss runs QURT on RISC-V; `dog_hal_moselle` = 0 hits; QURTK-on-wpss not published. Notes: QURT internals public via leaked Hexagon trees (not wpss); LibrePhone publicly documents the fake-PCI/WAKE transport framing (hif/wireless pages) — cite as partial context for the transport clause. |
| F-9 | code: `wpss.b07`, `wpss.b09` | LibrePhone ath11k/wireless pages (public WMI/HTT/HTC layering), GitHub | **UNIQUE-CONFIRMED** | Blob-side constant xref into wpss.bXX not published elsewhere. WMI-as-driver-blob-protocol is public knowledge (ath11k wmi.h, LibrePhone docs) — keep "first binary xref" framing. Attribution correction already recorded (F-19). |
| F-10 | fetch oeis.org/A399621, /A399620; web: `OEIS A399621 grid monochromatic rectangles 2-coloring` | OEIS entries, arXiv/AAAI/INTEGERS literature | **UNIQUE-CONFIRMED** | A399621 public state stops at row 8 ("0, 0, 2, 4, 12, 18, 30, 40"); A399620 has 8 terms, a(9) unknown, `more` keyword, no bounds. T(9,3..6)=3/6/16/24, 74<=a(9)<=80, LB(10,10)=130 not published anywhere. Caveat: A399621 last modified 2026-11-11 11:31 EST (today; history not retrieved — re-verify; if this is a pending lab submission, publish promptly). |
| F-11 | (operational notes) | VizieR/GCNS via search | **UNIQUE-CONFIRMED** | Practical/infra findings (I/364/gcns, TAP mirrors) — correct and non-overlapping. |
| F-12 | web: `Jeremy Alm "monochromatic rectangles" grid coloring minimum paper arXiv`; OEIS A399620 | OEIS, arXiv 2512.23303, SOCS 2021 | **UNIQUE-CONFIRMED** | a(9) open publicly; 74..80 bracket not published; no ILS/structural-evidence publication found. |
| F-13 | web: `"high proper motion" uncatalogued candidates Gaia DR3 survey 2025 2026 brown dwarf` | A&A 2025 Karpov, Gaia iow, arXiv | **UNIQUE-CONFIRMED** (method-overlap note) | Karpov 2025 (A&A 52011) mines uncatalogued high-PM UCDs from WISE epochs — same hunt, different regime (below Gaia limit). Cite it as related work; candidate list/epoch-aware vetting remains unpublished. |
| F-14 | web: `Qualcomm bluetooth firmware EVROS rampatch WCN6750 linux-firmware`; code: `CAMERA_ICP e_machine` | linux-firmware changelogs (Ubuntu 1.1.3-00069), gdrci/Research | **UNIQUE-CONFIRMED** (overlap note) | FP6 BT/TZ census not published. Notes: BT files themselves are public in linux-firmware (naming/ISA analysis is the lab's); gdrci (2026-10-08) documents a sibling platform's BT/WPSS firmware + build IDs — cite as related inventory. |
| F-15 | web: `Qualcomm AOP always-on processor RISC-V OR Hexagon core cpucp firmware architecture`; fetch github.com/linux-msm/xbltools | xbltools README, Qualcomm docs, ath11k list (Milos, Jan 2026) | **CORRECTION-NEEDED (partial)** | Generic "XBL = 3-component container (sbl1.elf+xbl_core.elf+xbl_sec.mbn)" is public via linux-msm/xbltools and coreboot createxbl.py; "Milos" SoC name public (linux-wireless list Jan 2026); Qualcomm docs describe AOP/CPUCP as microprocessors (Hexagon-toolchain assumption). Still unique: FP6 xbl.img 3-ELF ISA census, shrm/aop/cpucp = RV32 (contradicts public Hexagon assumption), rollback_index=Unix-epoch observation, SRoT/OEM-key chain. Scope the container/SoC-name clauses. |
| F-16 | code: `tinysys FreeRTOS mt6785`; web: MTK tinysys | mainline mtk_scp docs, Magisk/mtkclient | **CORRECTION-NEEDED (partial)** | Cortex-M4-based MTK companion cores (SCP) + small RTOS are public mainline knowledge; GFH/mtk_hdr magic 0x58881688 public (Magisk, mtkclient). Still unique: instruction-level Helio G95 tinysys ID, zero-ELF property of shipped MTK firmware, mtk_hdr chain mapping on production vendor images. Scope "first" to the device/blobs. |
| F-17 | web: `MediaTek camera CCU ARC processor Synopsys EM4` | Synopsys datasheets, Genio docs, community sources | **UNIQUE-CONFIRMED** | No public binary-level (ELF e_machine=195 / FPUDA ident) identification of MTK CCU firmware found; only soft community suspicion that CCU is ARC. Keep the claim; cite the soft prior suspicion if desired. |
| F-18 | web: `zrax socboot2 mtk_hdr MediaTek bootloader format GitHub` | Magisk docs (0x58881688), mtkclient, GitHub search | **CORRECTION-NEEDED (partial)** | zrax/socboot2 not publicly locatable (citation risk — verify or replace); mtk_hdr magic + GFH structs partially public (Magisk/mtkclient). "First vendor-image confirmation" should be scoped to full production-image chain mapping + dual-X.509 observation. |
| F-19 | code: `"0xc0691080"`, `wpss.b09` | GitHub code search, LibrePhone docs | **UNIQUE-CONFIRMED** | Negative-control xref methodology (adsp.b36) not found elsewhere; no third-party WMI-xref attempts found. |
| F-20 | code: `wpss.b07` (reprised) | GitHub | **UNIQUE-CONFIRMED** | Dispatcher construction-site search unpublished. |
| F-21 | web: same as F-13 | A&A 2025, CatWISE literature | **UNIQUE-CONFIRMED** (method-overlap note) | Blink/multi-epoch vetting is standard practice in the field; the 29 promoted objects + per-object 3-epoch evidence are unpublished. Same related-work citation as F-13. |
| F-22 | code: `"0xc0691080"` (0 hits), `wpss.b09` | GitHub, LibrePhone wpss.b09.md | **UNIQUE-CONFIRMED** | b09 registry ([b06-ptr, grp<<12\|cmdID, 0] at 0xc0691080) not public; LibrePhone explicitly failed to characterize b09 ("data file... PSX image"). |
| F-23 | code: `wpss.b07`/`wpss.b09` context | LibrePhone wireless.md (b06 "unknown architecture") | **UNIQUE-CONFIRMED** | b06=Hexagon consumer + per-group handler mapping not public anywhere. |
| F-24 | OEIS A399621 fetch (no 3-color variant); web searches as F-10 | OEIS, academic literature | **UNIQUE-CONFIRMED** | No published T_3 min-count values/bounds found (only the classical G_3=11 existence result). "First T_3 values/bounds" survives; caveat: re-check OEIS after today's A399621 edit. |
| F-25 | (object package; per-object SIMBAD screening already done in-lab) | Karpov 2025 as related work | **UNIQUE-CONFIRMED** | 29-object spectroscopy package unpublished; cite Karpov 2025 as method-level related work. |
| F-26 | code: `wpss.b09`, `"0xc0691080"` | GitHub | **UNIQUE-CONFIRMED** | b23/b24 structural unpack + NO-verdict confirmation unpublished; q6zip name is public knowledge (cited by the lab as suspected, unconfirmed — honest). |

## Corrections to apply (exact wording suggestions)

1. **F-1** — Replace "no published analysis of the wpss ELF headers exists" with:
   "no independent instruction-level analysis exists; the FSF LibrePhone project
   publishes hedged file-level identifications of the wpss.bXX ELF segments
   (docs/wpss.b07.md, 2026-01-16) including 'RISCV32 ?' and an i386 mislabel on b08."
2. **F-2** — Replace "No free public documentation exists for Hexagon/qdsp6 firmware
   internals" with: "Free documentation of Hexagon *firmware-image internals* (image
   format, QURT/RTOS structure) does not exist; Hexagon *ISA* PRMs are freely
   available on docs.qualcomm.com (V73 Jan 2024, V75, V79) and via QEMU/LLVM."
3. **F-5** — Drop "no public source documents this"; restate as "first public
   instruction-level proof (machine-mode RV32 startup at entry 0x404000), upgrading
   LibrePhone's hedged tool-level 'RISCV32 ?' identification (2026-01-16)."
4. **F-6** — Qualify: raw e_machine=94 values for CAMERA_ICP/vpu20/evass were
   published (gdrci/Research, 2026-10-08, labeled EM_XTENSA); the lab's increment is
   the historic-RISC-V interpretation, build/platform mapping, and family sweep.
5. **F-7** — Acknowledge LibrePhone's public i386 observation on wpss.b08; keep the
   systematic sweep + methodology prescription as the novel part.
6. **F-15** — Scope "xbl.img = 3-ELF container" against linux-msm/xbltools + coreboot
   createxbl.py (generic 3-component container is public); scope "SoC Milos" (name is
   public, Jan 2026 linux-wireless list); keep RV32 housekeeping-core IDs,
   rollback_index=Unix-epoch, and OEM-key chain as the unique parts.
7. **F-16** — Scope "first" to Helio G95 tinysys blobs (instruction level); cite
   mainline mtk_scp (Cortex-M4) and Magisk/mtkclient (0x58881688/GFH) as public
   partial knowledge.
8. **F-18** — Verify or replace the zrax/socboot2 citation (not publicly locatable);
   cite Magisk/mtkclient as partial public header knowledge.
9. **Ledger hygiene** — FINDINGS.md on main currently ends at F-22; F-23..F-26 rows
   are pending. Note the numbering conflict: commit c7443a6 calls the modem b23/b24
   unpack "F-25" while the working ledger numbering in the audit brief calls it F-26
   (F-25 = spectroscopy package). Reconcile before publishing rows.
10. **Track D** — Submit row 9 of A399621 and the a(9) bounds to OEIS promptly (the
    entry was edited 2026-11-11 by an unknown-to-us change; Jeremy F. Alm is active
    in exactly this area, Sep 2026 entries).

## Reproducibility

All queries and fetches were executed 2026-11-11 (UTC). Exact query strings are in
the table; key fetches: oeis.org/A399621, oeis.org/A399620, oeis.org/A272648,
librephone.fsf.org/site/wireless, librephone.fsf.org/site/ath11k,
github.com/fabiorafaelcoutada/librephone/blob/main/docs/wpss.b07.md,
github.com/linux-msm/xbltools; commit-date checks on fabiorafaelcoutada/librephone
(docs/wpss.b07.md -> 93d5d3f, 2026-01-16) and gdrci/Research
(peripheral_firmware_headers.txt -> 58d764f, 2026-10-08). GitHub code searches:
`wpss.b07` (322 hits — all packaging/inventory except LibrePhone docs),
`QURTK UTCB` (305 hits — leaked build trees only), `dog_hal_moselle` (0),
`wpss.b09` (16 — packaging/inventory only), `"0xc0691080"` (0),
`CAMERA_ICP e_machine` (350 — gdrci dump + kernel driver sources),
`CAMERA_ICP RISCV firmware`, `tinysys FreeRTOS mt6785` (0).
