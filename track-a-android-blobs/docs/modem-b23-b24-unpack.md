# modem.b23/b24 unpack attempt + WMI re-scan (closes the F-19 caveat)

**Claim:** F-19 left the two largest modem segments — modem.b23 (39,608,384 B) and
modem.b24 (28,947,136 B, 68 MB combined) — as "packed/compressed payloads,
contents unverified". This note maps their structure, attempts decompression,
and re-scans every verifiable byte with the 605-ID ath11k WMI xref. Result:
**b24's "packed" label was wrong** (90 % all-zero fill, all data literal and fully
scanned); **b23 is 745 KB literal islands + a 38.9 MB opaque body** that no
standard container opens and whose WMI-like hits behave like compressed-token
artifacts, not stored constants. **F-19's modem verdict (NO) stands**; the caveat
is closed to the extent statically possible.

**Date:** 2026-11-11. **Inputs:** `trees/modem/image/modem.b23`, `modem.b24`
(LineageOS FP6 mpss package), `instruments/ath11k/wmi.h` (605 IDs), scanner logic
reused from `tools/xref_wmi.py`. Analysis scripts one-off in `/tmp`; extracted
regions kept in `/tmp` only (nothing binary is committed).

## 1. Entropy + structure map (per-64 KB Shannon entropy)

| segment | blocks | zero (<0.1) | mid (3–7.5) | high (>7.5) | run structure |
|---|---|---|---|---|---|
| modem.b23 | 605 | 0 | 12 | 593 | H 0x0–0x2290000 · M 0x2290000–0x22f0000 · H 0x22f0000–0x2570000 · M 0x2570000–0x25d0000 |
| modem.b24 | 442 | 386 | 54 | **0** | Z 0x0–0x830000 · M 0x830000–0x980000 · Z 0x980000–0x1180000 · M 0x1180000–0x11c0000 · Z 0x11c0000–0x16f0000 · M 0x16f0000–0x1710000 · Z 0x1710000–0x1770000 · M 0x1770000–0x17a0000 · Z 0x17a0000–0x19f0000 · M 0x19f0000–0x1b90000 · Z tail |

- **b24 is not packed at all.** 87 % of its bytes are a single all-zero region
  (BSS-style fill); nothing anywhere exceeds entropy 7.5, i.e. there is no
  compressed region to open. Its five data islands are literal:
  - r1 0x830000–0x980000 (1.35 MB): Qualcomm **MCFG XML** (`mod="MCFG" cmd="MCFG_…"`
    visible in the raw bytes), strings: qmi ×1782, QMI ×80, wlan ×249, WLAN ×241,
    ath ×107, HTT ×19, MCFG ×6 — data/config tables, not code.
  - r2 0x1180000–0x11c0000, r3 0x16f0000–0x1710000, r4 0x1770000–0x17a0000:
    literal machine-code/table regions (entropy 3.5–6.5).
  - r5 0x19f0000–0x1b90000 (1.6 MB): dense binary, entropy ≤7.3, gibberish-only
    strings, **zero WMI-ID hits** — verdict-neutral.
- **b23** is high-entropy across 96 % of its extent with two ~384 KB mid-entropy
  (~5.0) literal islands (mid1 0x2290000–0x22f0000, mid2 0x2570000–0x25d0000).

## 2. Decompression results

Every standard container fails, everywhere:

- whole-stream zlib(±15)/gzip/bz2/lzma-alone/xz on both files: all fail at byte 0;
- gzip magic 1f8b08 (8 hits in b23), BZh (4), xz/lz4/zstd (0): none decompress;
- all 167 `5d 00 00` lzma-alone header candidates in b23 (≈70× the random rate,
  but none valid) and 34 in b24: **0 decompress**;
- all 5124/814 valid-FCHECK `78 xx` zlib candidates arise at the random rate
  (39.6 MB/256/31 ≈ 5000) and none yields a stream;
- sampled raw-deflate probe at 8 KB stride over both files: **0 successful windows**;
- `q6z`/`Q6Z`/`ZIC` string hits occur at chance level (≈1–2 per 3–4-byte pattern in
  39.6 MB) — no evidence of q6zip or any named Qualcomm container.

**Decompression yield: 0 bytes.** No chunk table or regular-stride repetition of
container headers exists in either file. The b23 body is opaque to every
verifiable-by-us format.

## 3. Re-scan of verifiable regions (605 IDs, aligned LE32)

| region | extent | names | distinct values | aligned hits | notes |
|---|---|---|---|---|---|
| b23 mid1 | 0x2290000–0x22f0000 | 82 | 51 | 324 | PDEV-dense (0x4004 ×13, 0x401f ×5, 0x4020 ×5, 0x400d ×4, 0x4001 ×3) |
| b23 mid2 | 0x2570000–0x25d0000 | 68 | 48 | 117 | TDLS 0x20002 ×5, 0x20003 ×3; SAP 0x30001 ×3; PROFILE 0x10002 ×4 |
| b24 r1 | 0x830000–0x980000 | 143 | 93 | 360 | PROFILE 0x10003/04/05 = 2/4/3; OBSS 0x40001 ×3; in MCFG/QMI XML region |
| b24 r2 | 0x1180000–0x11c0000 | 32 | 23 | 41 | mixed SCAN/PDEV/VDEV |
| b24 r3 | 0x16f0000–0x1710000 | 36 | 25 | 43 | P2P/DFS/SCAN mix |
| b24 r4 | 0x1770000–0x17a0000 | 7 | 6 | 7 | sparse |
| b24 r5 | 0x19f0000–0x1b90000 | 0 | 0 | 0 | dense binary, no hits |

b24 totals: 218 names / 147 distinct values / 451 aligned hits — all inside
literal bytes; F-19's whole-file b24 scan (177 matched) is therefore fully
explained by verifiable content. b23's literal islands add 150 names /
99 distinct values / 441 hits.

## 4. Why the b23 opaque body's hits are not stored WMI constants

F-19's whole-file scan found 366 matched IDs in b23, most *outside* the two
literal islands. Structural tests on the 38.9 MB high-entropy body:

1. **Isolation.** 0 of 71 aligned occurrences of 0x20001 (the highest-multiplicity
   hit) have any WMI-like neighbor word at ±4/±8 bytes; hits are spread over the
   whole 39 MB (median gap ≈122 KB) with random-looking 32-byte contexts
   (e.g. `a16da162 dc8058c7 c00b0080 501485f2 | 00004004 | 38ba9c84 a8b5a566`).
   Real constant tables cluster — mid1's 0x4004 ×13 sits in a tight run at
   0x22b62f0–0x22b9b20 with structured neighbors.
2. **No strings.** b23 yields 7,568 strings ≥8 chars and every sample is random
   ASCII gibberish (`lk&pIrALEMr`, `H(*XU;LiLOtZ`); zero protocol markers.
   Literal modem firmware cannot hide strings this way — b19 has 52 k, b24 has
   32 k (MCFG/QMI/wlan content). A body containing hundreds of stored WMI
   dispatch constants would carry the surrounding protocol text.
3. **16-bit distribution.** Slot fractions <0x8000/<0x1000/<0x100 are
   0.603/0.159/0.032 — well above uniform random (0.500/0.0625/0.0039) but below
   the literal regions (mid1 0.730/0.417/0.336; b24 r1 0.956/0.111/0.076). This
   between-profile is characteristic of byte-oriented compressed output (literal
   fragments carry partial skew; token streams skew small values), not raw tables
   and not uniform ciphertext.
4. **Weak but real repetition.** ≈500 duplicate 32-byte blocks per 8 MB window and
   repeated top words (0x10002000 ×199, 0x0040862f ×194 in the first 8 MB) —
   encrypted data has zero such repeats; literal code has thousands plus zero
   runs; compressed-with-tokens sits in between. Only 12 1-KB all-zero blocks in
   39 MB.
5. **Multiplicity math.** At 9.9 M aligned positions, 71 occurrences of one
   specific value cannot be random (expected ≈0.002); but isolation + gibberish
   contexts rule out a dispatch table. Byte-oriented LZ-style compressors
   reproduce aligned byte patterns when identical input fragments recur at
   similar token boundaries — which also explains 366 values matching.

Verdict: the b23 body is compressed/packed by an unidentified (very likely
proprietary, q6zip-like) scheme; its WMI-like values are compression artifacts
of the same generic Qualcomm constant families F-19 already neutralized via the
adsp.b36 control, not evidence of an ath11k WMI dispatch table. Even in the worst
case (body later proven literal), the values belong to the same non-specific
families present in the negative control, so the verdict does not change.

## 5. Verdict

- **F-19's modem answer stays NO (confirmed, caveat closed where possible).**
- b24: fully verified — no packed payload exists; all hits live in literal
  (uncompressed) regions, mostly the MCFG/QMI data island.
- b23: 745 KB literal islands verified (99 distinct values, same generic families);
  the 38.9 MB opaque body resists zlib/gzip/bzip2/xz/lzma/lz4/zstd at every
  candidate offset and shows no container, chunk table, string, or adjacency
  structure. The modem-WMI question does not reopen.

## Honest negatives / limits

- We cannot name b23's compression format; q6zip is suspected by profile but
  unconfirmed (no magic, no chunk table). Decompression yield is 0 bytes — the
  body remains byte-for-byte unverifiable, and this note argues from structure
  (isolation, strings, distributions), not from decrypting the payload.
- b24_r5 (1.6 MB, entropy ≤7.3, no strings) is dense but hit-free; it could be a
  lightly-compressed or table region — irrelevant to the WMI verdict.
- F-19's "matched IDs" counts distinct ID *names* (CMDID/EVENTID pairs share
  values); this note reports both names and distinct values to avoid ambiguity.
- Only stdlib compressors were tried; a hardware-proprietary scheme (e.g. q6zip)
  would need its decoder, which is out of scope here.

## Tool provenance

- Entropy/magic/decompression probes, region scans, 16-bit and adjacency tests:
  one-off scripts in `/tmp/scripts` (`map_b.py`, `extract_scan.py`,
  `region_scan.py`, `decisive.py`, `pair_test2.py`), fully reproduced in the
  tables above; extracted literal regions kept in `/tmp/decomp` (not committed).
- ID evaluation reused from `track-a-android-blobs/tools/xref_wmi.py` (F-9/F-19
  verified evaluator) against `instruments/ath11k/wmi.h`.
