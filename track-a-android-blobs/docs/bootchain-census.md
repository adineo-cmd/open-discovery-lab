# Boot-chain firmware census — Fairphone FP6 (QCM6490 "Lanai"/"Milos")

**Claim:** First public structural census (versions, ELF/container layout, ISA
identification, hashes, string inventory) of the FP6's boot-chain partitions:
`xbl`, `xbl_config`, `xbl_ramdump`, `uefi`, `abl`, `imagefv`, `shrm`, `aop`,
`aop_config`, `cpucp`, `cpucp_dtb`, `qupfw`, plus the Android boot images
`boot`, `vendor_boot`, `dtbo`, `pvmfw` and the AVB metadata `vbmeta`,
`vbmeta_system` from a public LineageOS OTA. Headline results: **the
housekeeping firmware on this SoC is 32-bit RISC-V** — `shrm` (Shared Resource
Manager), `aop` (Always On Processor), `cpucp` (CPUSS Control Processor) and
`aop_config` all carry `e_machine = 243 (EM_RISCV)` with the RVC ABI flag, and
`shrm`'s entry decodes as a textbook RV32 machine-mode startup (`auipc`/`addi`
gp-setup + `csrw mtvec`) — while `qupfw` alone claims `EM_QDSP6` (164,
Hexagon). **`xbl.img` is a multi-ELF container** (3 concatenated ELFs: outer
junk-header wrapper + an ELF32 RISC-V image + an ELF64 AArch64 image), matching
its stock name `xbl_s.melf` ("melf" = multi-ELF). The GKI `boot` kernel is a
**PE32+ EFI-stub AArch64 image**, and the whole family is one signed build
generation: `BOOT.MXF.2.1-02027-LANAI-1` (xbl/uefi/xbl_ramdump), signed with a
Qualcomm SRoT MBNv7 chain down to **Fairphone BV's own OEM attestation key**
("T2MO OEM Key", Amsterdam).

**Prior art checked (2026-11-10):** GitHub code search `BOOT.MXF.2.1-02027 OR
AOP.HO.5.0-00813 OR xbl_s.melf` — exactly **1 hit**, the
[DiamaneOS/diamaneos-tools](https://github.com/DiamaneOS/diamaneos-tools)
FP6 firmware inventory JSON (sizes/hashes/flash-order for delivery — no
structural analysis); its [FIRMWARE.md](https://github.com/DiamaneOS/diamaneos-tools/blob/main/docs/FIRMWARE.md)
documents partition *logistics* (flash order, A/B, rollback rules) but zero
image structure. `BOOT.MXF` (303 hits) = Project Mu UEFI platform ports
(WOA-Project/mu_andromeda_platforms SM8350, Project-Aloha Kodiak) —
reimplementation targets, not image analysis. `AOP.HO.` (167 hits) = firmware
dumps; one is a **source-tree dump** of the SDM710-era AOP
([Rivko/android-firmware-qti-sdm670](https://github.com/Rivko/android-firmware-qti-sdm670),
`AOP.HO.1.1.C1-00025`, 2020) whose build tree proves the AOP product line was
built with the **Hexagon/QDSP6 toolchain then** (scons `hexagon.py`,
`QDSP6BIN`, `HEXAGON_IMAGE_ENTRY`) — no public source states the ISA of the
QCM6490 generation. Kernel-side: mainline
`drivers/mailbox/qcom-cpucp-mbox.c` documents the AP↔CPUCP mailbox ("CPUSS
Control Processor") for sc7280/sm8450; `shrm` appears in vendor dtsi trees only
as a coresight trace probe (`tpdm_shrm`) — no firmware structure anywhere;
Qualcomm's own Linux boot docs list SHRM/AOP only as XBL log lines ("Image
Load, Start … Segments"). No public segment table, entry point, ISA statement,
or AVB descriptor inventory of any FP6/Lanai boot-chain image exists.

## Policy boundary (hard rule for this doc)

Census-only: file identity, versions, container/ELF/segment tables, ISA
identification at the entry-point level, hashes, and AVB **metadata facts**
(algorithm IDs, flags, rollback indices, descriptor partition names, key
presence + hash — **no key material is extracted or committed**). No
disassembly beyond entry sanity, no bypass content, no signature/ROM
vulnerability discussion.

## Method

1. `tools/payload_manifest.py` lists 37 OTA partitions (same tooling as
   [[bt-firmware-census]] / [[trustzone-census]]); `tools/payload_dump.py`
   dumped 18 partitions (15 firmware/AVB + `boot`/`vendor_boot`/`dtbo`)
   into `downloads/lineage-fp6/extracted/partitions-bootchain/` — beyond the
   task list, the manifest revealed `abl`, `xbl_ramdump`, `aop_config`,
   `cpucp_dtb`, `vbmeta_system`, all small and all included.
2. Header/container census + strings via a session parser (ELF32/64 headers +
   program headers; Android boot-image v3/v4; vendor-boot v4; dt-table;
   AVB0 headers/footers/descriptors). Full derived data in
   `results/bootchain-census.json`.
3. ISA sanity per the F-7 junk-header rule: `e_machine` claims cross-checked
   against entry-in-LOAD, `e_flags`, and RV32 opcode enrichment (fraction of
   words with valid RV32 opcodes vs the ~12.5 % random baseline), using the
   lab's two validated references: `wpss.b07` (RV32+C, F-5) and `modem.bXX`
   (Hexagon). No Hexagon/RISC-V disassembler is installed on the lab box
   (checked `objdump --info`, r2 — negative), so Hexagon-side identification
   rests on the registered `EM_QDSP6` value plus below-baseline RV32 density.

## Results

### Inventory

| partition | bytes | container | ISA claim (e_machine) | entry | QC version |
|---|---|---|---|---|---|
| xbl | 1,196,032 | **3 concatenated ELFs** | outer ELF32 mach=1 (junk, F-7); inner ELF32 **RISCV 243**; inner ELF64 **AArch64 183** | 0x22126000 / 0x20412d00 / 0x14825fa8 | BOOT.MXF.2.1-02027-LANAI-1 |
| xbl_config | 311,296 | ELF64, mach=1 (junk) | — (10 phdrs, 4×51,204-B LOADs) | 0x1494e000 | (none; name strings `pre/post-ddr-milos-1.0.dtb`) |
| xbl_ramdump | 860,160 | ELF64 AArch64 (sane) | **AArch64 183** | 0x81a40000 (= LOAD) | BOOT.MXF.2.1-02027-LANAI-1 |
| uefi | 2,904,064 | ELF64 mach=40 (junk: ELF64+ARM is an invalid combo) | AArch64 (EFI FV inside: `_FVH`, `DxeCore`) | 0xa7000000 (= LOAD) | BOOT.MXF.2.1-02027-LANAI-1 |
| abl | 245,760 | ELF32 mach=40 (EM_ARM) | ARM32 (self-consistent: entry = LOAD vaddr; instr-level unverified) | 0x9fa00000 | (payload opaque) |
| imagefv | 53,248 | ELF32 mach=40, entry 0 | payload wrapper (LOAD@0, 45,056 B, `_FVH` inside) | 0x0 | — |
| shrm | 53,248 | ELF32 **RISCV 243**, RVC flag | **RV32** (entry decodes: auipc/addi gp setup + `csrw mtvec` = csr 0x305) | 0x200000 (= LOAD) | contains "DDR_FW version : 19.12.0" |
| aop | 319,488 | ELF32 **RISCV 243**, RVC flag | **RV32** (AUIPC/ADDI pattern; opcode enrichment 26 %) | 0x13200000 (**outside all LOADs — flagged**) | AOP.HO.5.0-00813-LANAI_E-1 |
| aop_config | 20,480 | ELF32 **RISCV 243**, RVC flag | RV32 (entry in LOAD) | 0x81c82014 | — |
| cpucp | 204,800 | ELF32 **RISCV 243**, RVC flag | **RV32** (SYSTEM/JALR/AUIPC at entry; enrichment 38 %) | 0x17d0036c (in LOAD) | — (role strings: SCMI/RPMH/CPRh/Memlat/DTB parsing) |
| cpucp_dtb | 12,288 | ELF64 mach=1 (junk) | — (contains an embedded FDT: "cpucp_cfg.dtb") | 0x819f0000 (= LOAD) | — |
| qupfw | 61,440 | ELF32 **EM_QDSP6 164** | Hexagon per registered e_machine; RV32 density 5 % (below chance); instr-level unverified | 0x0 (junk or real) | — |
| boot | 100,663,296 | Android boot image **v4** | kernel = **PE32+ (0x20b), machine 0xAA64** EFI-stub, 35,711,488 B | — | os_version raw 0x200001aa; cmdline empty |
| vendor_boot | 100,663,296 | vendor boot **v4** | vendor_ramdisk 10,091,577 B; DTB region 3,641,222 B (8 FDTs found), dtb_addr 0x08500000 | — | cmdline `nosoftlockup sysctl.kernel.firmware_config.force_sysfs_fallback=1 bootconfig` |
| dtbo | 31,457,280 | dt_table (mkdtimg, **big-endian**) | 14 device-tree entries | — | — |
| pvmfw | 1,048,576 | Android boot image **v3** | payload = **raw AArch64 machine code** (ADR/MOVZ/SYSTEM encodings), no ELF wrapper, 768,576 B | — | — |
| vbmeta | 12,288 | AVB0 v1.0 | SHA256_RSA4096; **flags=3** (hashtree + verification disabled); one chain descriptor → `boot` | — | avbtool 1.3.0 |
| vbmeta_system | 4,096 | AVB0 v1.0 | SHA256_RSA4096; rollback_index = 1,788,566,400 = **Unix epoch of 2026-09-05**; descriptors for pvmfw/product/system/system_ext | — | avbtool 1.3.0 |

Full hashes, program-header tables, descriptor contents and signing metadata in
`results/bootchain-census.json`.

### Build identity

- **One XBL build ships xbl + uefi + xbl_ramdump**:
  `QC_IMAGE_VERSION_STRING=BOOT.MXF.2.1-02027-LANAI-1` in all three; OEM build
  hosts leak (`ip-10-195-202-206`, `T2M-NB-BY151`); `IMAGE_VARIANT_STRING=
  SocMilosLAA` — the SoC family name **"Milos"** is confirmed by xbl_config's
  own DTBs (`pre-ddr-milos-1.0.dtb`, `post-ddr-milos-1.0.dtb`) while build IDs
  use the target name **LANAI**.
- **AOP**: `AOP.HO.5.0-00813-LANAI_E-1` + `OEM_IMAGE_UUID_STRING=
  Q_SENTINEL_{...}_20250430_1132`. The `AOP.HO` product line existed in the
  Hexagon era (SDM710, 2020, `AOP.HO.1.1.C1-00025`) — the QCM6490 generation
  carries the same prefix but ships RISC-V-marked ELFs (see below).
- **Signing**: every image carries MBNv7 signature blocks with visible cert
  subjects — Qualcomm `SRoT MBNv7 Image Signing Root CA 6 (SubCA 10)`,
  `CASS - SBL40v0`, then an OEM chain: `Generated OEM Root CA` /
  `Generated OEM Attestation CA` → **`Fairphone BV`, `T2MO OEM Key`,
  Amsterdam** (validity 2025-03-05 → 2045-02-28). Per-image cert `notBefore`
  values range 2024-03-14 (qupfw) to 2026-08-31 (uefi/xbl_config/xbl_ramdump/
  imagefv/aop_config/cpucp_dtb) — the boot chain was refreshed in slices.

### The housekeeping cores are RISC-V (evidence quality per image)

`shrm`, `aop`, `aop_config`, `cpucp` all: ELF32, `e_machine = 243 (EM_RISCV)`,
`e_flags = 0x1` (RVC ABI flag), and RV32-opcode-enriched code. Strongest:
**shrm** — entry `0x200000` equals its RX LOAD and decodes as
`auipc gp …; addi gp; auipc …; addi …; csrw mtvec (csr 0x305)` — the same
machine-mode startup pattern F-5 validated on wpss. **cpucp** entry decodes
SYSTEM/JALR/AUIPC ops. **aop** shows the `auipc+addi` gp pattern in its code
LOAD but its `e_entry` (0x13200000) lies **outside all program headers** — the
header-level claim is strong, the entry field itself is not sane (flagged).
This is the **first public ISA identification** for any of these images on
this SoC; nothing public states what physical core runs them (the vendor docs
name SHRM/AOP only as boot-log lines; the kernel tree knows only the cpucp
mailbox and a tpdm_shrm trace probe). Contrast with F-5/F-6: wpss, camera ICP
and VPU on the same chip are also RISC-V — on QCM6490 the entire non-ARM
"small core" fleet we have now identified (wpss, aop, shrm, cpucp,
aop_config, xbl-embedded ELF) is RV32, and the only Hexagon claim left is
qupfw. The modem (Hexagon) and the BT rampatches (ARM32 Thumb) complete the
ISA map.

- **xbl's inner ELF32** (offset 0x1300 in the container): machine 243, entry
  0x20412d00 inside its own LOAD, LOAD start decodes `auipc/addi/auipc/jalr`
  — a RISC-V component embedded inside XBL itself. The inner ELF64
  (offset 0x2ef70, AArch64, 9 phdrs, RX LOAD 0xa3000 bytes at 0x14825000,
  entry in LOAD) is the classic XBL core. The outer wrapper (machine=1,
  2 phdrs covering only 4,748 B of a 1.2 MB file) is the F-7 junk-header
  pattern applied to a whole outer ELF.
- **qupfw**: `e_machine = 164` is the registered `EM_QDSP6` value (not a
  plausible filler like the 0/1/3 junk seen in F-7), its RV32 density is
  below the random baseline, and 11 RWX LOADs sit at low addresses
  (0x1000–0xb288) — consistent with a Hexagon serial-engine firmware, stated
  as "per header" because no Hexagon tooling is installed to verify
  instruction-level (tooling negative).

### AVB metadata (facts only)

- `vbmeta.img`: AVB0 v1.0, SHA256_RSA4096, `flags = 3` — both
  `AVB_VBMETA_IMAGE_FLAGS_HASHTREE_DISABLED` (1) and
  `AVB_VBMETA_IMAGE_FLAGS_VERIFICATION_DISABLED` (2) — the unlocked/userdebug
  LineageOS configuration; rollback_index = 0. Public key present, 1,032 B
  (RSA4096), sha256-16 `7728e30f50bfa5ce`. One chain descriptor (avb 3.4)
  naming `boot`.
- `vbmeta_system.img`: SHA256_RSA4096, same key hash, rollback_index =
  **1,788,566,400 = Unix epoch seconds of 2026-09-05 00:00 UTC** — matching
  boot's `com.android.build.boot.security_patch = 2026-09-05` property, i.e.
  the rollback index is the boot/GKI security-patch date as a timestamp
  (independently confirmed by DiamaneOS's FIRMWARE.md: "the security patch
  date as Unix time"). Carries hash/hashtree descriptors for **pvmfw, product,
  system, system_ext** and property descriptors:
  `com.android.build.{product,system,system_ext}.os_version = 16`,
  `.security_patch = 2026-10-01`, and
  `com.android.build.{system,product,system_ext,pvmfw}.fingerprint =
  Fairphone/lineage_FP6/FP6:16/BP4A.251205.006/43b742158d:userdebug/release-keys`.
- `boot.img`/`vendor_boot.img` carry AVB footers (`AVBf` v1.0) with embedded
  vbmeta: boot's (2,432 B at 35,717,120) is SHA256_RSA4096-signed with hash
  descriptor for `boot` (35,711,488) + properties (os_version 16, fingerprint,
  security_patch 2026-09-05); vendor_boot's (640 B at 0xd1c000) stores
  `algorithm = 0 (NONE)` with a hashtree descriptor for `vendor_boot`
  (13,746,176) — recorded as stored, interpretation out of scope.
- pvmfw is AVB-verified (descriptor in vbmeta_system) but **built from
  source** by LineageOS (also stated by DiamaneOS), so the stock↔OS AVB
  boundary is: firmware = Qualcomm/Fairphone signatures; OS partitions =
  LineageOS AVB with verification disabled at the top level.

### Kernel/OS-side cross-reference

- Mainline `drivers/mailbox/qcom-cpucp-mbox.c` ("CPUSS Control Processor
  (CPUCP) mailbox", sc7280/sm8450) is the AP side of cpucp's SCMI/RPMH
  surface — the role strings we found in cpucp (`SCMI init Done`,
  `RPMH driver init Done`, `CPRh init`, `Memlat init`, `DTB parsing Done`,
  `Boot Core-1 Done`) match the driver's purpose (cpufreq/cpuidle channel).
- `shrm` in vendor dtsi trees = `tpdm_shrm` coresight probe only; Qualcomm's
  boot docs mention SHRM image load/start lines. Its actual role here is
  evidenced in-image: **`DDR_FW version : 19.12.0`** — SHRM carries the DDR
  initialization firmware, and xbl_config carries the DDR training DTBs/DCBs
  — consistent with Qualcomm's docs statement that XBL performs DDR init.
- No upstream code parses any of these images' container formats; the
  `.melf` multi-ELF container and the monolithic-ELF partition images are
  undocumented publicly (checked negative).

## Negatives / open questions

- aop's `e_entry` (0x13200000) is outside all LOADs — junk entry field or a
  loader-side fixup; unresolved.
- xbl_config's four identical-size LOADs (51,204 B each) and its two embedded
  FDTs are catalogued but not decoded (multi-config layout suspected).
- vendor_boot v4 extension fields (ramdisk table offset/size, bootconfig
  offset/size): the table was located by content (1 entry, 108 B, at
  0xd1a000) but the field order of the extension was not decoded — the
  partition list in the OTA shows `vendor_boot` also holds
  `com.android.build.vendor_boot.fingerprint` as a property.
- dtbo's 14 entries not further decoded (board variant DTs).
- abl's payload region (237,568 B) yields no readable strings beyond certs —
  compressed or packed; ARM32 claim rests on the self-consistent ELF header.
- `storsec`, `toolsfv`, `vm-bootsys`, `vm-persist`, `logfs`, `study` appear in
  Fairphone's factory package (per DiamaneOS) but not in the LineageOS OTA
  payload — the OTA replaces only the OS-side images plus the firmware listed
  here (inventory delta noted, not investigated further).
- Exact boot image `os_version` raw field (0x200001aa) not decoded against
  the MAKE_OS_VERSION macro (values overflow the documented layout) — stored
  raw in the JSON.
- The vbmeta descriptor walk needed content-based enumeration: our minimal
  parser's descriptor-boundary walk mis-parses this avbtool 1.3.0 build
  (offsets differ from the classic layouts); all reported descriptor content
  is direct string/structure evidence, flagged in the JSON.

## Reproduce

```bash
python3 tools/payload_manifest.py payload.bin                 # 37 partitions
python3 tools/payload_dump.py payload.bin xbl xbl.img         # + uefi shrm aop …
python3 tools/payload_dump.py payload.bin boot boot.img       # + vendor_boot dtbo vbmeta*
# session parser (ELF/bootimg/AVB) — see results/bootchain-census.json for
# the full derived tables; ISA sanity = RV32 opcode enrichment vs the
# wpss.b07 (RV32) / modem.bXX (Hexagon) references per F-5/F-7
```
(Paths per lab layout: `downloads/lineage-fp6/extracted/partitions-bootchain/`.)
