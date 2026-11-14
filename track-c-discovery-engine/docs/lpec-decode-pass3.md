# LPEC decode pass 3 — LP bit layout RESOLVED, byte-exact frame parse on both LPEC samples

Track: track-c-discovery-engine / format-re / LPEC (Sony DVF/MSV voice codec)
Artifact: `results/format-re/lpec-census/lpec-decode-pass3.json`, `results/format-re/lpec-census/lpec_decoder.py`
Prior passes: F-47 (packet/frame census), F-48 (LPEC.dll + codebook inventory), F-49 (SP layout, pump semantics)

## Claim

The LPEC per-frame bit layout is **resolved for both modes** (LpecLp 8 kHz / 6 kbps and LpecSp 16 kHz / 16 kbps). Every field width and order is derived from LPEC.dll code and confirmed empirically: a stdlib parser implementing the derived layout consumes **100% of the audio region of both decodable samples with zero residual bits, zero invalid frames**, implies exactly 6000.1 / 16000.0 bps, and reproduces F-47's arithmetic (2426196 = 50545 frames; 20352 = 159 frames). F-47's MSV-16k open question ("frame size among 24/48/128") is closed: **128 B type-0 frames** (with 96/160 B type-1/2 frames interleaved). F-47's "per-packet reset + 6-byte trailer" container model is **refuted** (parity argument + byte-exact continuous parse); the stream is continuous and frames straddle packet boundaries.

This is still **not a PCM decoder**: the per-subframe pulse payload (a derived-size block of 8-bit pulse-position codes + sign bits) is parsed at frame level but its intra-block split needs one more allocator mirror, and no synthesis (codebooks, LSP expansion) is implemented. Every transmitted bit, however, is now accounted for.

## Method

1. Decompiled the remaining LPEC.dll read path from the F-48 Ghidra project (pyghidra, analyze=False reuse): core `FUN_10005040`, LSP read `FUN_10005bf0`, gain read `FUN_10005ca0`, pitch read `FUN_10005d50`, pulse reader `FUN_100060e0`, bit-budget allocator `FUN_10004450`, config `FUN_10003e60` (setparams), table config `FUN_1000df10`. Sony binaries/decompiled code not committed; derived facts only.
2. From setparams: mode selection by sample rate — fs<=8000: LSP = 3 groups x 6 bits, gain field 7 bits, 8 pitch bands, order 10; fs>8000: 4 x 6, 8 bits, 10 bands, order 16. Gain bits = 7 + (fs/8000)*0x78 thresholds (7 @8k, 8 @16k, 9 @32k).
3. From setparams: per-type bit targets at state+0x1c/0x20/0x24/0x28 = round(fs-frame-bits) x {1, 3/4, 5/4, 1} = 384/288/480/384 (LP) and 1024/768/1280/1024 (SP) — **identical to CUnitter's LpecLp/LpecSp nibble tables 48/36/60/48 and 128/96/160/128 bytes**. The 2-bit frame type IS the mode nibble's source.
4. Field walk per type (see layout table below); the pulse budget per subframe is *derived*, not stored: `floor((T - C)/2) - excitation_cost - 19`, where 19 = state+0x14 (0x13) pitch bits and FUN_10004450 allocates the subframe budget into 8/10 bands as N0 x 8 + N1 x 8 + N2 x 8 + N3 x 1 bits read by FUN_100060e0.
5. Implemented the parser (`lpec_decoder.py`, stdlib only) with the container layer from F-47, and validated on the two LPEC samples (TRC files excluded — different codec, dsp_trc.dll).

## Layout (per frame, MSB-first)

`T` = per-type bit target; `C` = bits consumed so far in the frame; excitation cost = 8 (page present) or 1 (absent); pitch block = 7-bit lag-scale index + 6-bit pitch-row A + 6-bit pitch-row B (19 bits/subframe, both modes).

| type | bytes LP/SP | fields after 2-bit type |
|---|---|---|
| 0 | 48/128 | 1 LSP-mode bit; LSP set(s) 3x6 (LP) / 4x6 (SP) — one set if mode=0, two if mode=1; gain sub1 = 7 (LP) / 8 (SP) bits, 0 = muted, else +6-bit gain-shape index; gain sub2 same; exc sub1 = 1 presence [+7-bit codebook page]; exc sub2 same; sub1 pitch 7+6+6; sub1 pulses = floor((T-C)/2) - exc_cost - 19; sub2 pitch 7+6+6; sub2 pulses = same formula; tail pad = (T-C mod 2) + exc_cost (2/3, 9/10, or 16/17 bits) |
| 1 | 36/96 | LSP set; gain sub2 only; sub2 pitch 7+6+6; sub2 pulses = T-C-19; pad 0 |
| 2 | 60/160 | LSP set; gain sub1; gain sub2; sub1 pitch + pulses = floor((384/1024 - C)/2) - 19; sub2 pitch + pulses = (480/1280) - C2 - 19; pad 0 |
| 3 | 48/128 | LSP set; gain sub2 only; sub2 pitch 7+6+6; sub2 pulses = T-C-19; pad 0 |

Structural correspondence with SP (F-49): identical field order and widths except LSP groups (3 vs 4), gain width (7 vs 8) and bit targets; the LP "missing lag field" was FUN_10005d50's 7+6+6 pitch block, present in both modes.

## Validation

- **budgtele.dvf** (LpecLp): 2393 packets, audio 2426196 B -> **50545 frames, byte-exact closure** (frame sum == audio == parse end), 0 invalid. Types: 43479 x 48 + 5917 x 48 + 573 x 36 + 576 x 60. Implied 6000.1 bps @ 64 ms frames.
- **07011600.MSV** (LpecSp): audio 20352 B -> **159 frames, byte-exact closure**, 0 invalid. Types: 155 x 128 + 2 x 96 + 2 x 160. Implied 16000.0 bps. Resolves F-47's MSV open item.
- **Tail-pad signature**: type-0 tail pads observed ONLY {3, 9, 17} bits (43479 LP frames) — exactly the derived `(T-C) mod 2 + excitation_cost` with parity driven by the number of present excitation pages; types 1/2/3 pad exactly 0. A single wrong field width anywhere would break this signature.
- **Per-packet reset refuted twice**: 1014 B packet areas cannot tile by {48,36,60} or {128,96,160} (all even, 1014 odd after /2); continuous parse closes byte-exact. F-47's 6-B "trailer" is the head of the frame straddling into the next packet; F-47's phase-lock evidence (368/400) is consistent with 48-B-dominant continuous frames.
- **Musical plausibility (budgtele LP)**: gain values cluster 32-50 (speech levels) with 0 = 13.9% (mute/comfort frames), no uniform noise; excitation pages present 20.7%, spread over 0..127 (top pages 60/17/73 — no degenerate repetition, matching F-47's "no static silence code"); voiced lag-scale indices cluster ~30-43; LSP indices use full 0..63. MSV gains reach 192 — direct empirical proof of the 8-bit SP gain field vs 7-bit LP.

## Honest negatives

- Pulse payload is parsed as one opaque block per subframe (exact at frame level; intra-subframe boundary known to <8 bits). Full split needs mirroring FUN_10003d80 (per-band pulse allocation from the WAV table at state+0x10c) + FUN_10004450's balance steps.
- No synthesis: LSP expansion (FUN_100064b0/FUN_10004b10), excitation page decode (FUN_10004960: 4-segment pitch interpolation over pages at state+0xc8 + idx*0x40), LPC synthesis (FUN_1000f640/FUN_1000f1c0/FUN_10005af0) and the ~15 codebook tables per mode are inventoried (F-48) but not wired up.
- The 7-bit pitch field indexes a 128-entry double table at state+0xcc (a lag-dependent scale); its exact pitch-lag mapping is unquantified.
- 6-B-per-packet DD/NN header counter semantics (F-47) remain unknown.
- TRC samples (taxis, Pinkston) excluded: 24-B/10 ms frames belong to dsp_trc.dll/PVoice.dll, a different codec.

## Next levers

1. Decompile FUN_10003d80 + FUN_10004450 tables (0x10c WAV table, 0xcc/0xd0/0xd4) to split pulse blocks; then FUN_10004960 + pages to reconstruct excitation; LSP expansion + synthesis for PCM. All tables already extracted in F-48's JSON.
2. Encoder-side Rosetta (FUN_100065b0 path) for ground-truth loops.
3. crc/checksum: none observed at frame level (tail pads are pure padding), closing F-47's "48-bit checksum" hypothesis as padding.
