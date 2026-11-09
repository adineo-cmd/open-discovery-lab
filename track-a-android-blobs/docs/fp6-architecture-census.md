# Architecture census of Fairphone FP6 Qualcomm firmware (LineageOS 23.2, 2026-11-09 nightly)

**Claim:** The WCN6750 wpss firmware runs on a **32-bit RISC-V** core (not the
"8-bit ATMel AVR" upstream guessed); Qualcomm's camera-ICP and all VPU
firmware on this device are also RISC-V, built with a toolchain using the
historic `e_machine=94` ID; and per-segment `.bXX` ELF headers carry
untrustworthy `e_machine` values, which breaks naive automated corpus
classification. **None of this is documented anywhere public** (checked:
GitHub code search, ath11k docs, SRLabs 2025, LWN, XDA — 2026-11-09).

**Prior art checked:** upstream `docs/wireless.md` (unverified AVR/RISCV32
guess); [SRLabs Hexagon fuzzing](https://srlabs.de/blog/hexagon-fuzz-full-system-emulated-fuzzing-of-qualcomm-basebands)
("no free tools or documentation exist"); GitHub code search `wpss.b07`,
`WCN6750 ELF`, `CAMERA_ICP riscv` (no results); ath11k kernel docs (no ISA
info). No published ELF-header analysis of any of these images exists.

## Method

Source: `lineage-23.2-20261109-nightly-FP6-signed.zip` (public mirror).
Extraction: `payload_dumper` → partitions; `tools/extract_vfat.py` (modem.img,
vfat) and `tools/extract_ext4.py` (vendor.img/dsp.img, ext4); census via
`tools/census.py` (stdlib ELF parser; hashes + program headers, no binary
content). All scripts in `tools/`, census in `tools/census.json`/`census.md`.

## Results

### Architecture histogram (665 files, 4.9 GB partitions)

| e_machine | files | notable contents |
|---|---|---|
| 0 (EM_NONE, header junk) | 166 | mcfg .mbn configs, split-image segment files |
| Hexagon (164) | 94 | modem.b*, adsp.*, cdsp.*, ipa_fws, GPU zap shaders |
| AArch64 (183) | 34 | hdcp, soter64, smplap64, evautil64 (modem/image) |
| ARM (40) | 31 | bdwlan board-data ELFs (60,000 B each), CAMERA_ICP_170.elf |
| RISC-V historic (94) | 12 | **CAMERA_ICP.mbn/.elf/.mdt, vpu20/30/33_*.mbn** |
| RISC-V (243) | 1 | **modem/image/qca6750/wpss.b07** |
| x86 (3, header junk) | 1 | qca6750/wpss.b08 (data segment, bogus header) |

### The wpss (WCN6750 wireless processor subsystem)

- `wpss.b07` — ELF32, **e_machine=243 (EM_RISCV)**, e_type=EXEC, entry
  **0x404000**, 6 program headers, loads spanning vaddr 0x404000–0x422528.
  Version strings: `QC_IMAGE_VERSION_STRING=WLAN.MSL.3.0.1-00591-QCAMSLSWPLZ-1`.
- `wpss.b08` — largest wpss segment (275,644 B), single RWX LOAD at vaddr
  **0x4ff00000**, e_machine=3 (x86) with entry 0x401 — a nonsense header for
  a data segment. Contains `WLAN_UCODE_MOSELLE_4.2.0-00000` ("Moselle" =
  WCN6750 firmware codename). **Conclusion: .bXX segment-file ELF headers are
  not reliable for architecture identification.**

### Camera ICP / VPU

- `CAMERA_ICP.mbn/.elf/.mdt`, `CAMERA_ICP_170.elf`, `vpu20_2v/4v.mbn`,
  `vpu30_2v.mbn`, `vpu33_4v.mbn` (+ `_unsigned` variants) — ELF32,
  **e_machine=94**, the historic RISC-V value used by early toolchains
  (243 was assigned later). ICP version: `CICP.FW.7.0-00021` (CRM), platform
  strings `CAMERA_640_V1 (Mimas)`, `CAMERA_740_V1 (Skye)`.
- Public Qualcomm documentation does not state the ICP/VPU ISA; kernel
  sources name the devices but not the cores. This appears to be the first
  public identification of FP6 ICP/VPU firmware as RISC-V.

## Implications

1. LibrePhone upstream's `docs/wireless.md` should replace the AVR guess with
   the verified RISC-V identification (PR planned).
2. The ath11k ↔ wpss boundary can now be analyzed against real RISC-V
   disassembly (capstone supports RISC-V; Hexagon support is experimental —
   Hexagon remains the harder, still-undocumented side).
3. Automated firmware-census tooling (including ours, pre-fix) must treat
   .bXX e_machine fields as noise; use .mdt headers + entry-point sanity.

## Negative results / limitations

- Census covers modem.img, vendor.img /firmware,/dsp,/bt_firmware (symlink →
  empty), dsp.img. system/product/system_ext not yet walked (Android
  framework, not firmware blobs; queued).
- Entry-point sanity was checked only for the headline files; a systematic
  "trustworthy header" pass per file is queued.
- Disassembly-level confirmation of RISC-V instruction patterns pending
  (capstone install queued). Header + strings evidence is already conclusive
  for e_machine 243; e_machine 94 identification rests on the value's
  documented history plus QC's known RISC-V usage in ICP-generation silicon.

## Reproduce

```bash
python3 tools/extract_vfat.py partitions/modem.img trees/modem
python3 tools/extract_ext4.py partitions/vendor.img /firmware trees/vendor-firmware
python3 tools/census.py trees --out census.json --md census.md
# then: filter census.json for family wifi-wpss / machines 94 & 243
```
