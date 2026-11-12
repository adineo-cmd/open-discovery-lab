# DiamondWare Sound Toolkit (.dwm/.dwd) — format census (F-40, Track C, R-9)

Census date: 2026-11-13. Samples: NOT committed (all in /tmp only).

## Prior art (Rule 0, dated 2026-11-13)

- dexvert `src/format/audio/diamondWareDigitized.js` (repo SHA b126fe4f, read
  2026-11-13): covers `.dwd` only, converters `ffmpeg[libre][format:dwd]`,
  `awaveStudio`. The R-9 `.dwm` target has no dexvert module.
- **libsndfile has a DWD reader** (`src/dwd.c`): present in vendored copies of
  libsndfile 1.0.19 (read 2026-11-13 via LostMoho/Papagayo vendored tree).
- **FFmpeg-family DWD demuxer** (`libavformat/dwd.c`): read 2026-11-13 via
  librempeg mirror (SHA e77bbc4d); added in the FFmpeg 4.4 cycle (2021-2022
  per changelog references). Probe: 24-byte magic; header parse: rate@0x20
  u16 LE, channels@0x22, bps@0x23, duration@0x2A u32, data offset@0x2E u32.
- **archive.org item `DiamondWaresSoundToolKit_1020`** (stk12.zip, item dated
  1995; fetched + extracted 2026-11-13): the DiamondWare Sound ToolKit 1.02
  demo SDK. Contains: `PLAYDWM.C` v1.02 (1994-10-21 to 1995-04-11, Keith
  Weiner & Erik Lorenzen — vendor's own DWM player source), `DWS.H`,
  `STKMAN.DOC` (93,781 B demo manual), `MID2DWM.EXE` (MIDI type-1 → DWM
  converter), `PLAYDWD.*`, `VOC2DWD.EXE`, `SAMPLE_DWM` (byte-count-identical
  to the mirror's SAMPLE.DWM), `SAMPLE_MID` (its MIDI source).
- **KEY BOUNDARY FINDING**: the demo manual states the *purchased* product
  ships "full file specifications on our .dwd and .dwm file formats"
  (STKMAN.DOC line 85). The demo manual itself contains NO byte-level DWM/DWD
  layout (grep-verified 2026-11-13) — the spec was print-only and is not on
  the public web. So: `.dwd` = fully code-documented (libsndfile/FFmpeg);
  `.dwm` = publicly UNSPECIFIED ("derived from MIDI" per the Just Solve wiki
  page, read via search summary 2026-11-13), vendor parser source exists only
  inside the 1995 SDK. R-9's "wrapped-MIDI decode open" is CONFIRMED for
  public documentation.

## Samples

7 DWM from `sembiance.com/fileFormatSamples/music/diamondWareDigitizedMusic/`
(combat, LAKE, LBL5, MC07, SAMPLE, SPAC1, TOWN; 390-12782 B) + 4 DWD from
`.../audio/diamondWareDigitized/`.

## DWD verification (SOLVED — already documented)

4/4 samples match the code-documented layout exactly: magic
`DiamondWare Digitized\n\0\x1a`, compression byte 0x1F=0 (uncompressed PCM),
rate 5000-22050 Hz, mono, 8-bit, and `duration_samples × block_align ==
filesize − data_offset` holds EXACTLY in 4/4 (offsets 56/64). Novelty of the
`.dwd` side: none (identification+decode solved upstream).

## DWM census (7/7 files)

- Magic `"DiamondWare Music\0"` (18 B).
- **Header length (arithmetic crack)**: u32 LE at 0x24 = 74 / 85 / 96 / 107
  and byte 0x2A = 2 / 3 / 4 / 5 — exactly `74 + 11×(0x2A−2)` in 7/7. The
  header extends by an 11-byte record per unit beyond the 74-byte base;
  the 0x18 u32 LE body-length field then equals
  `filesize − header_length` in 7/7 (verified: 3461/498/305/3145/12686/
  9788/3759). The 11-byte extension records sit at 0x4A+ and carry
  `XX 31 4f 00 ...`-shaped tokens echoing the constant signature block —
  instrument/DWD-sample reference candidates (MID2DWM takes an .IBK patch
  bank; DWM songs reference named DWD instruments).
- 0x14-0x17: per-file u32 (random-looking) — ID/checksum candidate.
- 0x1C u32 LE: 68-2613 (event/counter field, ~3× the parsed note motifs).
- 0x20 = 52 constant; **0x34-0x3B constant `21 31 4f 00 f2 d2 52 73` in 7/7**
  (toolkit signature).
- 0x28 u16 LE = 720 / 728 / 750. 728 == MID2DWM's documented 72.8 Hz timer
  rate × 10 (manual documents 18.2/36.4/72.8/145.6 Hz heartbeat rates) —
  candidate timer-rate field (×0.1 Hz). UNCONFIRMED.
- Byte 0x2A ∈ {2..5}: header-extension record count (above).
- Body entropy 3.3-4.35 bits/byte across all 512 B blocks — structured event
  stream, NOT compressed audio.
- Body event motifs (partial): recurring 6-byte note-like records
  `[06|09][note 0x25-0x40][inst][vol][dur u16 LE]` — durations 9-22 ticks
  (≈124-302 ms at 72.8 Hz), combat.dwm notes 0x27-0x2E = bass-register run;
  interleaved multi-voice phrases; marker bytes 0xad/0x87/0x93/0xf0-0xf9
  (instrument/patch or control class candidates). Full grammar UNRESOLVED.

## Crack verdict

- RESOLVED: container (extended header arithmetic, magic, signature block),
  DWD layout (verified against 4 samples), body type (event stream, not
  compressed audio).
- PARTIAL: DWM event grammar (one 6-byte note motif characterized; control
  events, tempo mapping, 0x1C field semantics open).
- NEGATIVE: no public .dwm decoder found anywhere (2026-11-13); dexvert
  detects .dwm but lists no converter; ffmpeg `dwd` handles .dwd only.

## Next steps

1. Disassemble `MID2DWM.EXE` (ships in the 1995 SDK) — it *writes* DWM; its
   output code is the byte-level spec. PLAYDWM.C → DWS_LIB (74 KB, shipped)
   contains the reader.
2. Seek the commercial STK manual (print-only DWM/DWD spec, per demo manual).
3. Cross-check tempo field hypothesis against SAMPLE_MID ↔ SAMPLE_DWM pair
   (both in the SDK — a conversion pair for differential RE).
