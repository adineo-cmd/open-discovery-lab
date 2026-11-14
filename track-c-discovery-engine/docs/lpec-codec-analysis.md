# Sony LPEC / TRC voice codec — bitstream structural first pass (F-47-or-next-free)

Date: 2026-11-14. First serious structural attack on the Sony LPEC/TRC voice bitstream (F-34 open prize). Bounded first attempt: the container-to-codec boundary is now mapped; the codec interior is not decoded. Honest negatives included.

## Claim

The DVF/MSV audio payload is a fixed-size frame stream inside 1024-byte transport packets with a 10-byte packet header. Frame sizes close the bitrate arithmetic exactly for two of three variants: TRC/PVoice 19200 bps = 24-byte frames at 100 fps (10 ms); LPEC/STVoice 6000 bps = 48-byte frames at 15.625 fps (64 ms). The LPEC 16000 bps (ICD-BM1 MSV) frame size is unresolved among {24, 48, 128} bytes. Silence is per-frame comfort noise (no deterministic silence code). No open-source decoder exists; the reference decoders are Windows-only DLLs (PVoice.dll, STVoice.dll) — that boundary is documented, not crossed.

## Prior art (dated)

- MultimediaWiki "MSV" page, last edited 2009-04-11 (wiki.multimedia.cx/index.php/MSV): only public bitstream-level write-up. States 1024-byte packets beginning `00 xbyte 00 0A 04 00 0E 30 81 cbyte`, derived from a single sample, listed under "Undiscovered Audio Codecs". This session confirms the pattern on all 4 corpus files, decodes `bytes[4:6]` as the payload-size field, extends the constant `0E 30 81` to a per-file triple (`0E 30 81` / `0C 46 68` / `10 3D A4`, unset `FF FF FF` on taxis.dvf), and partially decodes `xbyte` (NN) — see below. Wiki's cbyte = our slow per-packet counter.
- PRONOM Research submission, 2023 (github.com/digital-preservation/PRONOM_Research, Sony Voice Recorders): identification BOF patterns only; states formats "can only be played and converted using Sony software". No codec content.
- preservation.tylerthorsted.com, 2023-04-21 ("Sony Voice Recorder"): documents the preservation problem; LPEC expansion given as "Long-term Predicated Excitation Coding" (Sony trademark). Container-level only.
- GitHub code search re-verified 2026-11-14 (`LPEC`, `MS_VOICE`, `sony dvf`): no decoder, no codec tables, no TRC parser. dexvert (Sembiance, repo updated 2026-11-12) identifies/converts via external Sony tools only. F-34 "no open-source decoder" verdict stands.
- Reference implementations are Windows-only binaries: PVoice.dll (TRC writer), STVoice.dll (6 kbps LPEC), Sony ICS Converter / Digital Voice Editor / Sound Organizer. Not analyzed here (Windows-only boundary; no samples of the DLLs in scope this session).

## Method

4 samples fetched 2026-11-14 from sembiance.com/fileFormatSamples/audio/sonyCompressedVoiceFile/ (the complete public dir; sizes match F-34 census exactly): 07011600.MSV (LPEC 16000, ICD-BM1), WelcometoPinkstonMiddleSchoolLibrarytest.dvf (TRC 19200, PVoice.dll), budgtele.dvf (LPEC 6000, STVoice.dll), taxis.dvf (TRC 19200, PVoice.dll). Stdlib Python only: header/TOC parse, stride autocorrelation, per-packet best-phase test, consecutive-frame Hamming similarity, entropy per byte/nibble/bit-position, silence-window scan, exact-repeat block search. Script: results/format-re/lpec-census/analyze_lpec.py. Samples not committed.

## Findings

### 1. Packet layer (all 4 files)

- Audio region = sequence of 1024-byte packets. First packet at file offset 0x400, or 0x800 when a 1 KB 0xFF fill block precedes it (Pinkston, taxis — an empty annotation/index slot).
- Packet header, 10 bytes: `00 NN | 00 0a | SIZES | AA BB CC | DD`.
  - bytes[4:6] BE u16 = bytes used in this packet INCLUDING the 10-byte header. 0x0400 = 1024 on full packets; <1024 on the final partial packet: MSV 82, Pinkston 442, budgtele 718, taxis 40. First public statement of this field's meaning.
  - `00 0a` constant in all files. `AA BB CC` = per-file constant triple (device/codec tag; 0xFF unset on taxis). `DD` = slow monotonic counter, +1 per ~2 s (MSV 8c→91 across 21 packets = 1 per 4 packets = 2.048 s; budgtele 48→5b ≈ 1 per 1.85 s; Pinkston e7→e9 ≈ 1 per 2.1 s; taxis 0xFF unset). Semantics unresolved.
- NN (byte 1), decoded as deterministic per-packet counter:
  - taxis and Pinkston (both TRC): identical strict 12-cycle over packets: 0a, 4c, 46, 40, 3a, 34, 2e, 28, 22, 1c, 16, 10 (decimal 10, 76, 70, 64, 58, 52, 46, 40, 34, 28, 22, 16): step −6, wrap +72 (equivalently mod-78 arithmetic skipping 4). Two independent recordings, same sequence → content-independent.
  - MSV: NN = (10·k + 10) mod 128 verified for k = 0, 2..20 (values 10, 30, 40, ... 130→12→22...); packet 1 anomalous (0x34 = 52 where formula gives 20).
  - budgtele: −6 descending runs over {58, 52, 46, 40, 34, 28, 22, 16, 10} with irregular wraps and occasional +6 / −18 steps (about 10 deviations in 90 packets) — the only content-correlated candidate.
  - Semantics unresolved; hypotheses: encoder buffer level, segment countdown, or phase accumulator.
- TOC tag 4 entry corrected (F-34 listed it as unverified `ae030004` junk): format is `[04][u24 BE unused-tail][u32 BE audio-bytes]` where unused-tail = 1024 − last-packet size field. Verified exactly on 3 files: MSV 1024−82 = 942 = 0x3ae; Pinkston 1024−442 = 582 = 0x246; budgtele 1024−718 = 306 = 0x132.
- Trailer after audio end: MSV 942 B of high-entropy data (index/metadata block, unverified); Pinkston 582 B, budgtele 306 B, taxis 984 B of 0xFF.
- Pre-audio metadata region (0xB0–0x400) carries 'SONY CORP.' marker plus per-file strings: 'Ortap' (MSV), 'Jane Ann Knowles' (Pinkston annotation), 'koko' (budgtele), 'SONY ICD-P330F' (taxis device model — taxis was written by an ICD-P330F, a recorder not in the F-34 census model list).

### 2. Frame layer

| variant | bitrate field | frame size | autocorr peak (vs ~0.0039 noise) | frame rate | bitrate closure | total data B = N × frame |
|---|---|---|---|---|---|---|
| TRC 19200 (PVoice, taxis+Pinkston) | 19200 | 24 B = 192 bits | 0.057 at 24 (14.6x); harmonics 48/72/96 | 100 fps = 10 ms | 192×100 = 19200 exact | Pinkston 12600 = 525×24 exact; taxis 80136 = 3339×24 exact |
| LPEC 6000 (STVoice, budgtele) | 6000 | 48 B = 384 bits | 0.0291 at 48 (7.5x); only multiples of 48 | 15.625 fps = 64 ms | 384×15.625 = 6000 exact | 2426196 = 50545×48 + 36 (final frame truncated) |
| LPEC 16000 (ICD-BM1, MSV) | 16000 | UNRESOLVED: {24, 48, 128} | weak 0.0088 at 128 (1.9x) only | 64 ms if 128 B | any of 128×15.625 / 48×41.667 / 24×83.33 = 16000 | 20352 divisible by all three (848×24, 424×48, 159×128) |

- Full packet data area = 1014 B (1024 − 10 header). 1014 = 42×24 + 6 = 21×48 + 6: per-packet frame reset with a 6-byte trailer (positions data[1008:1014]) OR a continuous frame stream straddling packets. Evidence favors reset-with-trailer: per-packet best-phase test locks to offset 0 (Pinkston 9/13 packets, budgtele 368/400 packets) where straddle predicts phase cycling 6/12/18; trailer bytes are statistically random (consistent with a 48-bit checksum, not padding — padding would be constant). Straddle predicts exact totals equally well. Unresolved; the 6-byte trailer contents are the discriminator.
- MSV 64-ms hypothesis: budgtele (LPEC 6000) and MSV (LPEC 16000) would share the 15.625 fps / 64 ms frame rate with different frame sizes (48 vs 128 B) — the only cross-variant constant observed. Weak 128-B autocorr peak supports it; absence of strong repetition (unlike budgtele) means ICD-BM1's encoder emits no repeated silence code. Marked UNRESOLVED.
- Frame interior: no per-frame mode/header byte anywhere (hypothesis (b) refuted — data areas are uniformly high-entropy with no repeated anchor bytes).
- Bit-position P(1) shows per-variant bias structure: budgtele bits 6-7 strongly zero-biased (0.368/0.375 vs 0.44-0.50 elsewhere) — consistent with sub-byte codes (e.g., 6-bit payload + 2-bit tag) packed MSB-first; MSV bits 3-4 mildly biased (0.397/0.403); TRC near-uniform. Nibble high/low entropy both exactly maximal (3.671) in all files → nibble-symmetric, dense bit-level packing (hypothesis (c) partially supported: byte-aligned frame boundaries, bit-packed interior).
- Byte entropy of audio payload: MSV 7.884, Pinkston 7.853, budgtele 7.802, taxis 7.936 — confirms F-34's 7.7-7.9 dense-packing observation.

### 3. Silence (F-34 follow-up)

- No byte-identical repeated frames in any audio region (exact-repeat scan at 24/48 B found only trailing 0xFF container pad). LPEC/TRC silence = per-frame comfort noise: the encoder emits a fresh low-level code every frame. There is no static "silence code" to use as a Rosetta anchor; the F-34 "silence floors" are low-entropy speech regions (lowest 384-B windows: H 6.85-7.35), not deterministic frames.
- Rosetta consequence: known-plaintext attacks need actual audio alignment (device-recorded WAV vs LPEC of the same utterance), not silence.

## Hypotheses tested (per mission order)

1. (a) Fixed-frame container with per-frame sub-codecs: SUPPORTED. 1024-B transport packets, fixed-size codec frames (24 B TRC; 48 B LPEC-6k; MSV unresolved), frame count closes total byte counts exactly.
2. (b) Byte-aligned frames with a mode byte: REFUTED. No mode byte at packet or frame level; entropy maximal; no repeated anchors in data areas.
3. (c) Purely bit-packed stream: PARTIAL. Frame boundaries are byte-aligned multiples; interiors are dense bit-level (nibble symmetry, biased trailing bits in budgtele). Neither pure byte-code nor pure bitstream.

## Honest negatives

- LPEC 16000 (ICD-BM1) frame size not determined ({24, 48, 128} all arithmetically consistent).
- 6-byte per-packet trailer semantics unknown (checksum? side-info?), and reset-vs-straddle not definitively settled.
- NN counter semantics unknown (deterministic, content-independent for TRC).
- Codec interior (quantization tables, prediction, codebooks) untouched — 7.8-7.9 bits/byte with no visible byte structure cannot be reversed from 4 samples alone.
- Sampling rate unknown (8 kHz assumed in prior art, unverified; frame durations imply 192/384-sample frames if 8 kHz).
- Windows-only reference decoders (PVoice.dll, STVoice.dll, ICS Converter, Digital Voice Editor, Sound Organizer) not obtained or analyzed — boundary documented per mission scope.

## Next lever (named)

1. PVoice.dll / STVoice.dll static analysis (Ghidra, 32-bit x86): extract LPEC codebooks/quant tables from rdata; the DLLs ship inside Sony Digital Voice Editor / ICS Converter installers (Windows-only; run under Wine for extraction). This is the single highest-yield next step for a real decoder.
2. Known-audio Rosetta: device-record WAV + Sony-tool-encoded DVF of the same clip → frame-wise known-plaintext (needs Sony software or an ICD device; bypasses silence-code absence).
3. 6-byte trailer: brute CRC-16/32/48 variants against the 1008-byte data areas (cheap, offline, uses existing samples) → settles reset-vs-straddle and packet integrity model.
4. MSV 16k frame size: one longer ICD-BM1 recording with exact duration metadata, or per-packet phase test once a repetition signal exists.
