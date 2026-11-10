# Bluetooth firmware census — Fairphone FP6 (QCM6490 / WCN6750)

**Claim:** First public version, architecture, container-format and segment
documentation of the FP6's Bluetooth firmware family. The FP6 ships its entire
BT firmware family in a dedicated `bluetooth` partition (FAT16) holding
**two generations of Moselle (WCN6750) firmware plus a third "EVROS" combo
family that upstream Linux does not know how to name**; the rampatch headers
decode cleanly against `btqca.h` and their `rom_build` fields map to the
kernel's own `rom_ver`→filename math; and the `.mbn` ELF patches are
**32-bit ARM (Thumb-2)** — a different core than the RISC-V wpss on the same
chip. `msbtfw12.*` and all `evr*` files are **absent from linux-firmware**.

**Prior art checked (2026-11-10):** GitHub code search `msbtfw11` (420 hits —
all packaging: linux-firmware WHENCE forks, pmaports/pacstall APKBUILDs,
distro file lists, LibrePhone `docs/files.md` file list — zero analysis);
`evrbtfw20 OR evrnv20` (3 hits: a file list and two Qualcomm vendor-HAL
source dumps); `BTFW.EVROS OR BTFW.MOSELLE` (2 hits: raw `ver_info.txt`
device dumps, e.g. [ChkDumps/redmi_flute_dump](https://github.com/ChkDumps/redmi_flute_dump),
metabuild dated 2025-12-25 — version *strings* only, no structural work);
linux-firmware `qca/` tree (has `msbtfw11.mbn/.tllv` + `msnv11.bin` at
*different sizes* than FP6's — different builds — and **no msbtfw12, no
evr\* files**). No public source documents the architecture, segment layout,
or header structure of any of these images.

## Method

1. The BT firmware is **not** in the trees the lab had already extracted:
   `vendor/bt_firmware` is an empty symlink, and the census had zero BT-named
   files. The firmware lives in the dedicated `bluetooth` OTA partition.
   We parsed the OTA `payload.bin` manifest without protobuf
   (`tools/payload_manifest.py`) and dumped the partition with the new
   `tools/payload_dump.py` (REPLACE/REPLACE_XZ/bzip2 ops; the type-1 op is
   **bzip2**, not brotli — verified by the `BZh9` magic).
   Validation: re-dumping the `modem` partition reproduces the existing
   payload_dumper output **byte-for-byte** (sha256 `8a329c30…`, 89 ops).
2. `bluetooth.img` is a **FAT16 filesystem** (864,256 B) — extracted with the
   lab's `extract_vfat.py`; 11 files.
3. Census (`tools/census.py`) + TLV/NVM decode (`tools/bt_tz_analyze.py`),
   decoding against the upstream `drivers/bluetooth/btqca.h` struct layouts
   (fetched from kernel.org gitweb, 2026-11-10).

## Results

### File inventory (`bluetooth` partition, `image/` directory)

| file | bytes | sha256 (16) | content |
|---|---|---|---|
| msbtfw11.mbn | 210,724 | (results JSON) | ELF32 ARM rampatch, Moselle 1.1 |
| msbtfw11.tlv | 198,512 | " | same patch in TLV container |
| msbtfw11.ver | 34 | " | `BTFW.MOSELLE.1.1.2-00064-PATCHZ-2` |
| msnv11.bin | 6,366 | " | NVM config, Moselle 1.1 (66 tags) |
| msbtfw12.mbn | 112,788 | " | ELF32 ARM rampatch, Moselle 1.2 |
| msbtfw12.tlv | 100,576 | " | same patch in TLV container |
| msbtfw12.ver | 34 | " | `BTFW.MOSELLE.1.2.0-00380-PATCHZ-1` |
| msnv12.bin | 6,316 | " | NVM config, Moselle 1.2 (64 tags) |
| evrbtfw20.tlv | 48,769 | " | TLV rampatch, EVROS 2.0 |
| evrnv20.bin | 8,331 | " | NVM config, EVROS 2.0 (67 tags) |
| evrbtfw20.ver | 35 | " | `BTFW.EVROS.2.0.0-00143-PATCHZ-5_DEF` |

(Full hashes + decoded headers in `results/bt-tz-census.json`.)

### Architecture (first public statement for this family)

Both `.mbn` files: **ELF32, e_machine = 40 (EM_ARM)**, e_type = EXEC, with
three program headers and a single RWX `LOAD`:

| file | entry | LOAD vaddr | LOAD filesz |
|---|---|---|---|
| msbtfw11.mbn | 0x24c51 | 0x24c50 | 0x30724 (198,436 B) |
| msbtfw12.mbn | 0x23dc5 | 0x23dc4 | 0x18894 (100,500 B) |

Entry = LOAD vaddr **| 1** → **ARM Thumb entry point**. Unlike the modem's
`.bXX` segment files (see [[fp6-architecture-census]] F-7), these are
complete, self-consistent ELF files (sane e_type/e_machine/entry), so the
ARM identification is trustworthy without .mdt cross-checks. Contrast: the
WCN6750 **wpss on the same chip is 32-bit RISC-V** (F-5) — Qualcomm's BT and
WLAN cores on this SoC are different ISAs. Nothing public states what CPU the
WCN6750 BT firmware executes on; this is the first published identification.

### TLV rampatch header decode (against `btqca.h` structs)

| field | msbtfw11.tlv | msbtfw12.tlv | evrbtfw20.tlv |
|---|---|---|---|
| type (`type_len & 0xff`) | 1 = TLV_TYPE_PATCH | 1 | 1 |
| length field | 198,508 (= size−4) | 100,572 (= size−4) | 48,765 (= size−4) |
| format_version / signature | 1 / 0 | 1 / 0 | 1 / 0 |
| download_mode | **3 = QCA_SKIP_EVT_VSE_CC** | 3 | 3 |
| product_id | **21** | 21 | **29** |
| rom_build | 0x0101 | 0x0102 | 0x0200 |
| patch_version | 0x89fd (35,325) | 0x8b04 (35,588) | 0x8c69 (35,945) |
| entry (@ container offset 0x24) | 0x00024c50 | 0x00023dc4 | 0x20027fc8 |

- **The `entry` field of the TLV equals the ELF entry minus the Thumb bit**
  (0x24c50↔0x24c51; 0x23dc4↔0x23dc5): the `.mbn` and `.tlv` are the same
  firmware payload in two containers, confirmed numerically.
- **rom_build → filename:** upstream `btqca.c` computes
  `rom_ver = ((soc_ver & 0xf00) >> 4) | (soc_ver & 0xf)`. With
  rom_build = 0x0101 → 17 = 0x11 → `msbtfw11`; 0x0102 → 18 = 0x12 →
  `msbtfw12`; 0x0200 → 32 = 0x20 → `evrbtfw20`. **The kernel's own math
  reproduces all three filenames from the shipped binaries.** First time
  this correspondence is shown against real firmware headers (upstream
  documents the formula but no public source ties it to the files).
- The on-device patch header is 32 bytes before data (entry at offset 0x24),
  i.e. the vendor containers carry 12 more bytes (reserved fields) than the
  upstream 24-byte `struct tlv_type_patch`; decode accordingly.
- EVROS entry **0x20027fc8** sits in the classic Cortex-M SRAM window
  (0x2000_0000+) and appears with companion pointers 0x200117b7/0x20017xxx —
  a different load layout than Moselle's 0x24c50 region.

### NVM files

All three decode as TLV tag sets (`tlv_type_nvm`): **tag 1 (64 B) is the
firmware version string** (e.g. `BTFW.MOSELLE.1.1.2-00064-PATCHZ-2`),
**tag 2 is 6 bytes — the BD address slot** (the Android vendor BT HAL
`PatchDLManager::ReadTlvInfo` writes the device BD address into tag 2 before
download). msnv11: 66 tags; msnv12: 64; evrnv20: 67 tags *and* an outer
**type-4 enclosing TLV header** plus 903 trailing bytes — matching the HAL's
multi-NVM/`TLV_TYPE_BT_FM_NVM` unwrapping path, which upstream kernel
`btqca.c` does not implement.

### Kernel ↔ firmware cross-reference (drivers/bluetooth, kernel.org, 2026-11-10)

- `btqca.c` `qca_uart_setup` for **WCN6750**: rampatch = `qca/msbtfw%02x.mbn`
  **preferred as an ELF patch** (ELF patches force
  `QCA_SKIP_EVT_VSE_CC` — segments are send-only, a synthetic
  command-complete is injected), fallback `qca/msbtfw%02x.tlv`; NVM =
  `qca/msnv%02x.bin`. All three filename families on the FP6 partition map
  onto this logic except `evr*`.
- **No `evr` string exists anywhere in upstream btqca.c/hci_qca.c.** The
  consumer of `evrbtfw20.tlv` is Qualcomm's **Android vendor BT HAL**
  (`vendor.qti.bluetooth@1.x` `patch_dl_manager.cpp` — present in public
  AOSP-derived proprietary dumps), which picks patch paths from a
  `chipset_ver → PatchPathInfoMap_` table not shipped in the HAL source we
  could see. So: **FP6 ships a second combo BT chip family (EVROS, product
  ID 29) that the Linux mainline stack cannot name or select.**
- The same `ver_info.txt` dump that lists Moselle builds also lists
  `wlan_evr: WLAN.EVR.1.0-01270-QCAEVRSWPLZ-1` — EVROS has its own *WLAN*
  image family (`QCAEVRSWPLZ`) alongside the Moselle WLAN family
  (`QCAMSLSWPLZ`, the one in `wpss.b07`): EVROS is a full WLAN+BT combo chip
  shipped alongside WCN6750 on Lanai-family (QCM6490) boards. Its exact chip
  identity is **not established** here — flagged for follow-up.
- linux-firmware (tree listing fetched 2026-11-10) ships
  `msbtfw11.mbn` 202,508 B / `msbtfw11.tlv` 190,296 B / `msnv11.bin` 5,899 B
  — **all different sizes from the FP6 builds** (210,724 / 198,512 / 6,366),
  and **no msbtfw12, no evr files**. Fairphone FP6's BT family is not fully
  covered by linux-firmware.

## Negatives / open questions

- Which SoC is EVROS (product_id 29)? Not decidable from the partition
  alone; needs the HAL's chipset-version map or a device with a named
  verinfo. (Candidates per kernel enum naming: none match "evr".)
- `msbtfw11.mbn` contains two `NULL` phdrs (vaddr 0x58000 / 0x3e000,
  filesz 0x1208 each) besides the code LOAD — likely embedded TLV/signature
  blocks; not further decoded (out of census scope for now).
- The kernel selects between msbtfw11/msbtfw12 by the controller-reported
  `rom_ver` at runtime; both are shipped so either ROM revision boots. Which
  one FP6's chip actually requests is only observable at runtime.
- No gatekeeper partition/image found in the FP6 payload (see
  [[trustzone-census]]).

## Reproduce

```bash
python3 tools/payload_manifest.py payload.bin          # 37 partitions
python3 tools/payload_dump.py payload.bin bluetooth bluetooth.img
python3 tools/extract_vfat.py bluetooth.img trees-bt/
python3 tools/census.py trees-bt --out bt.json
python3 tools/bt_tz_analyze.py trees-tzbt trees-tzbt/census-tzbt.json
```
(Paths per lab layout: `downloads/lineage-fp6/extracted/…`.)
