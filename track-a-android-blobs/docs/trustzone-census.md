# TrustZone firmware census — Fairphone FP6 (QCM6490)

**Claim:** First public census (versions, ELF/segment structure, hashes,
string inventory) of the FP6's TrustZone firmware family. On this device the
TrustZone stack ships as **monolithic AArch64 ELF partition images — no
`.mdt`/`.bXX` split at all**: the QTEE OS (`tz` partition, 4,034,560 B, 45
program headers), the QHEE hypervisor (`hyp`, entry 0x80000000), the
KeyMaster TA (`keymaster`), the device-config blob (`devcfg`) and the
QSEE TAs `uefisecapp`, `multiimgoem`, `featenabler`. QTEE and QHEE are one
build: `TZ.XF.5.28.0-00021-LANAIAAAAANAZT-1` (git `be6181077ac3`) — the same
build ID already visible (as a raw string) in a public Redmi device dump of
the same Lanai/QCM6490 family, but never documented or analyzed.

**Prior art checked (2026-11-10):** GitHub code search `LANAIAAAAANAZT OR
TZ.XF.5.28` (18 hits — **all** `board-info.txt` files in Xiaomi-family device
dumps: ChkDumps/redmi_flute_dump, redmi_malachite_dump, poco_peridot_dump,
nothing_asteroids_dump, … — raw build IDs, zero analysis); earlier lab
searches (fp6-architecture-census, 2026-11-09) found no ELF-header analysis
of any QCM6490 image. Public TrustZone literature (QSEE reverse-engineering
papers, kernel qseecom work) documents the *protocol*, not any of these
images' structure. **No public segment table, entry point, or hash inventory
of an FP6/Lanai QTEE/QHEE/KeyMaster image exists.**

## Policy boundary (hard rule for this doc)

This is a **census-only** document: file identity, versions, ELF/segment
tables, hashes, and build-string inventory. **No disassembly, no code-level
reverse engineering of TrustZone internals, no key/DRM material, no bypass
content** — the same clean-room rule the lab applies to DRM. Everything below
is derivable with `readelf`-level tooling from a public OTA.

## Method

1. The TrustZone family was missing from the extracted trees (the lab's
   census covered modem/vendor/dsp only). `tools/payload_manifest.py` lists
   all 37 OTA partitions; `tools/payload_dump.py` dumps them (validated
   byte-identical against the reference `modem.img` extraction — see
   [[bt-firmware-census]]).
2. Dumped partitions: `tz` (4,034,560 B), `hyp` (1,683,456 B), `keymaster`
   (442,368 B), `devcfg` (49,152 B), `uefisecapp` (200,704 B), `multiimgoem`
   (12,288 B), `featenabler` (106,496 B).
3. Census + strings via `tools/census.py` / `tools/bt_tz_analyze.py`;
   hashes and full segment tables in `results/bt-tz-census.json`.

## Results

### The images are plain ELFs (a format change worth documenting)

Modern QSEE images on this platform are **single ELF64 files**, not the
`.mdt + .bXX` PIL split the older images (and most public tooling) expect:

| partition image | bytes | sha256 (16) | ELF | e_type | entry | phnum |
|---|---|---|---|---|---|---|
| tz.img (QTEE) | 4,034,560 | (JSON) | AArch64 | EXEC | **0x14693000** | **45** |
| hyp.img (QHEE) | 1,683,456 | " | AArch64 | DYN (PIE) | **0x80000000** | 7 |
| keymaster.img | 442,368 | " | AArch64 | DYN (PIE) | 0x0 | 9 |
| devcfg.img | 49,152 | " | AArch64 | EXEC | **0x1c000000** | 4 |
| uefisecapp.img | 200,704 | " | AArch64 | DYN | 0x0 | 9 |
| multiimgoem.img | 12,288 | " | **ELF32 ARM** | **0 (junk, per F-7)** | 0x149fd000 | 3 |
| featenabler.img | 106,496 | " | AArch64 | DYN | 0x0 | 9 |

Segment highlights (full tables in the results JSON):

- **tz.img**: 45 phdrs, two load regions — `0x1469xxxx–0x158e9xxx`
  (code+data, entry region) and `0x1c0xxxxx–0x1c44xxxx` (a second RWX/XR
  region; devcfg's entry 0x1c000000 targets the same 0x1c region, i.e.
  devcfg data lives adjacent to QTEE's secondary region).
- **hyp.img**: PIE with entry 0x80000000 — the long-documented QHEE load
  base — plus DYNAMIC/TLS segments; read-only data at vaddr 0xe00000.
- **keymaster.img / uefisecapp.img / featenabler.img**: classic PIE TA
  layouts (XR text LOAD at vaddr 0 + WR data LOADs + GNU_RELRO).
- **multiimgoem.img**: ELF32 ARM with e_type = 0 (ET_NONE) and flag-less
  LOAD at 0x149fd000 — another instance of the junk-header rule (F-7): the
  census "ELF32 ARM" reading is real, but the header is not fully sane.

### Versions and build identity

- `QC_IMAGE_VERSION_STRING=TZ.XF.5.28.0-00021-LANAIAAAAANAZT-1` +
  `OEM_IMAGE_VERSION_STRING=be6181077ac3` in **both** tz.img and hyp.img —
  one TZ build ships the OS and the hypervisor. `LANAI` = QCM6490-family
  target name (also visible in `LPAIDSP.HT.1.0-01090-LANAI-1` etc. in the
  Redmi flute verinfo); `LANAIAAAAANAZT` is the TZ-specific target variant.
- The same QTEE build ID string is already public in device dumps'
  board-info/verinfo files (18 GitHub repos) — as opaque strings. This
  census is the first to tie it to the actual ELF images, segment layout,
  and hashes.
- keymaster.img: no QC build-ID string; identity is `keymaster64` (string)
  + command-name table (`KEYMASTER_SPU_INIT`, `KEYMASTER_PROVISION_ATTEST_KEY_NEW`,
  `KEYMASTER_SET_VBH`, `KEYMASTER_SPU_SSR`, `Keymaster Pre Shared Secret`,
  …) — an attestation/SPU-capable KeyMaster TA. Android-keymaster version
  fields (`osVersion`, `OS_VERSION`, `system_version`) present.
- tz.img embeds `KeymasterLite_*` (an in-OS keymaster-lite module) and a
  dense `tzbsp_*` (TrustZone BSP) + `qsee_*` vocabulary
  (`TZ_QSEE_LOG`, `qsee_open`, `qsee_prng_getdata`…).

### In-tree TrustZone users (from modem/image, family "other" in census)

- **soter64** (61,408 B payload, `.mdt+.b00-.b08` split — MDT format lives
  on for TAs shipped inside the modem tree): SOTER device-attestation TA
  (`construct_soter_sign_data`, `/persist/data/soter/`, `SOTER_CE`).
- **smplap64** (1,653,528 B payload): Qualcomm's **"sample app"** (smplap)
  crypto/test TA — `tz_app_crypto_aes_*`, `qsee_malloc` — a development
  sample shipping in a production device.
- **UUID-named TAs** `05B04A44-…`, `FD719D50-…`: secure-element service TAs
  (`CESEService_*`, `GPQESE_Open/Transceive` — GlobalPlatform SE API);
  `32552B22-…`: no strings ≥8 chars.
- **featenabler** appears **twice**: as its own `featenabler` partition
  (merged ELF, 9 phdrs) and split (`featenabler.mdt + .b00–.b08`) in
  modem/image. The 9-segment vaddr/filesize tables match exactly and
  spot-checked segments are byte-identical — same TA, two packaging forms.
  Function: per-SoC feature licensing (`soc_hw_version`, `FeatureEnabler_*`,
  RPMB-backed).
- No `gatekeeper` image exists anywhere in this payload; keystore-related
  functions live in keymaster.img + QTEE's KeymasterLite.

## Kernel-side cross-reference

- Upstream Linux gained Qualcomm QSEECOM support (drivers/tee/qcom,
  `qseecom.c`, merged in the v6.8 era per public kernel history) that
  loads/calls QSEE apps via the `qsee` interface — the TA images documented
  here are the userspace side of that ABI. No upstream code parses the
  images themselves; nothing in the kernel tree describes their ELF layout.
- The QSEE `.mdt`-split TA format is the one the older qseecom (Caf)
  sources handled; the modern **monolithic-ELF** partition images above are
  loaded by the bootloader/UEFI stage, not the kernel — which is why no
  kernel-side naming exists for them (nothing to xref against; stated as a
  checked negative).

## Policy-sensitivity note

Widevine/DRM (`widevine.mbn`, `hdcp*`) are **excluded from scope here**
(census rows exist in `tools/census.json` under family `drm`; the lab's DRM
work is docs-only per the track table). This document contains no
TrustZone code analysis, no keys, no bypass guidance.

## Negatives / limitations

- tz.img has 45 phdrs; the census JSON lists the first 32 (census.py
  `max_phdrs=32` cap) — remaining 13 are same-region WR/XR segments, not
  re-run for this pass (queued).
- No version string in devcfg.img / uefisecapp.img / featenabler.img /
  multiimgoem.img beyond function names — build IDs for the TAs are
  apparently not carried in-image.
- EVROS/BT companion doc: [[bt-firmware-census]].
- Not yet dumped (out of this pass's scope, flagged for the queue):
  `pvmfw` (protected-VM firmware), `uefi`, `xbl*`, `shrm`, `cpucp`,
  `imagefv`, `aop*` — boot/TZ-adjacent families with the same monolithic
  ELF pattern expected.

## Reproduce

```bash
python3 tools/payload_manifest.py payload.bin
python3 tools/payload_dump.py payload.bin tz tz.img      # + hyp keymaster devcfg uefisecapp multiimgoem featenabler
python3 tools/census.py trees-tzbt --out census-tzbt.json
python3 tools/bt_tz_analyze.py trees-tzbt trees-tzbt/census-tzbt.json
```
