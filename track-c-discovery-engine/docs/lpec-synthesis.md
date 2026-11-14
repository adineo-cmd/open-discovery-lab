# LPEC synthesis pass — first open-source PCM output from .dvf/.msv (plausibility-validated)

Track: track-c-discovery-engine / format-re / LPEC (Sony DVF/MSV voice codec)
Artifact: `results/format-re/lpec-census/lpec_synthesis.py`, `results/format-re/lpec-census/lpec-synthesis.json`
Prior passes: F-47 (container census), F-48 (LPEC.dll API + table inventory), F-49/F-50 (bit pump, CUnitter framing), F-51 (bit-exact frame parser)

## Claim

The LPEC synthesis path is now **wired**: `lpec_synthesis.py` consumes the F-51 bit-exact frame parser, reconstructs per-frame LSF vectors from the LPEC.dll codebook stages, converts LSF→LPC (public Chebyshev P/Q math), interpolates LSFs across each frame exactly as Sony's `FUN_1000f1c0` does (16 linear steps, or 2×8 steps prev→avg→cur for dual-LSP frames), and produces PCM16. Both decodable samples convert end-to-end with **exact duration match** (budgtele.dvf: 50545 frames → 3234.88 s = expected; 07011600.MSV: 159 frames → 10.176 s = expected), zero PCM saturation, and good frame-boundary continuity (LP mode: mean frame-edge RMS jump 70.3 vs 65.4 interior baseline — no clicks). To our knowledge this is the **first open-source LPEC decoder to produce audible audio**. Honesty: this is **plausibility-validated, not sample-validated** — no Sony decoder output was available as ground truth; the excitation fine structure (pulse positions/values, comb post-filter, pitch pulse shaping) is approximated, so the output has the correct spectral envelope, pitch periodicity, and energy structure, but is not sample-accurate.

## Method

1. Decompiled the remaining synthesis interior from the F-48 Ghidra project (pyghidra, project reuse, ~30 functions total): `FUN_10004960` (page cross-fade), `FUN_10005ca0` (gain read), `FUN_10005bf0` (LSP read), `FUN_10005d50` (subframe excitation assembly), `FUN_100064b0`/`FUN_10004b10` (double/int16 LSF expansion), `FUN_1000f1c0` (interpolated LSF→LPC + synthesis), `FUN_1000f430`/`FUN_1000e4a0` (comb post-filter), `FUN_1000f640` (held-buffer cross-fade), `FUN_10004450`/`FUN_10003d80` (band pulse allocator), `FUN_100060e0`/`FUN_1000f4e0` (pulse reader/placer), `FUN_100096c0`/`FUN_10009dd0` (LSF repair + LSF→LPC), `FUN_1000df10`/`FUN_10003e60` (table install + setparams). Sony binaries/decompiled code not committed; derived facts only.
2. Key semantic corrections over the F-49/F-51 reading (from decompile, all now exact):
   - The **LSF codebook** is four stage tables (state+0xb4/0xb8/0xbc/+0xc0) of 64×order doubles, added stage-wise (FUN_100064b0); values are normalized cycles/sample (0..0.5; confirmed by the int16 path scale 65536.0). Stage 0 rows are monotone (base VQ), stages 1–3 are decreasing-range residual VQ — verified: stage-sum monotone on 2030/2030 LP and 283/284 SP real frame index sets.
   - The **"gain" field is not a gain**: the 7/8-bit value is a *pitch lag* driving an IIR comb post-filter (FUN_1000f430 reads 3 taps computed from the lag by FUN_1000e4a0; g=0 bypasses), and the 6-bit shape field indexes a [64][3]-doubles table (state+0xc4 via pointer) plus a [64][3]-shorts table (state+0x124).
   - The **"pitch" block** carries the excitation amplitude envelope: 7-bit index → 128-entry double scale table (state+0xcc); 6-bit rows A/B → per-band (8/10) amplitude rows (state+0xd0/+0xd4, stride bands×8 B, 64 entries each), band amp = rowB+rowA, clamped ≥1e-5 (FUN_10005d50), applied per band time-segment of the subframe.
   - **Frame structure**: 512 samples @8 kHz / 1024 @16 kHz; three gain segments per frame ([held-lag, sub1-lag, sub2-lag] = [1/8, 1/2, 1/4] of the frame per the three FUN_1000f430 calls); LSF state slides (+0x260→+0x150 via FUN_10005af0); the excitation cross-fade blends current and held buffers via 8-double "pages" (idx×0x40 B at the state+0xc8 pointer, 4 segments each) or a plain A84/A88 cross-fade when pages are absent (FUN_10004960/FUN_1000f640).
   - **Constants extracted**: avg weight 0.5; pulse sign ±0.6; PCM round 0.5, clamp ±32767/−32768; int16 LSF scale 65536.0.
3. Implemented `lpec_synthesis.py` (stdlib): PE parser → runtime table extraction from the user-owned LPEC.dll (no table values committed), LSF stage sum + min-gap repair, LSF→LPC via the P(z)+Q(z) Chebyshev recursion **including the (1±z⁻¹) factors** (an initial implementation without them produced unstable filters — the single biggest wiring bug found and fixed in the one iterate), per-step direct-form synthesis, best-effort excitation, PCM16 writer.

## Validation (no ground truth — plausibility battery)

| check | budgtele.dvf (LpecLp 8k/6k) | 07011600.MSV (LpecSp 16k) |
|---|---|---|
| frames / duration | 50545 → 3234.88 s = expected 3234.88 s | 159 → 10.176 s = expected 10.176 s |
| PCM saturation | 0 samples | 0 samples |
| normalization scale applied | ×49.5 | ×39.5 (same order of magnitude) |
| frame-edge RMS jump vs interior | 70.3 vs 65.4 (no clicks) | 528.6 vs 74.7 (bursty file: attack transient at frames 1–3, then near-silence with occasional bursts) |
| energy structure | continuous speech-level variation (RMS 70–240), no degenerate flatness | loud onset, quiet tail — plausible for a recorder capture |
| spectral centroid (crude) | ~2000 Hz @8k | ~4000 Hz @16k (both ≈ fs/4, crude metric) |
| comb-lag (ex-"gain") stats | 19.4% of subframes g=0 (unvoiced/muted), voiced lags plausible F0 range | 28/318 g=0; lags up to 213 samples = ~75 Hz F0 @16k |

## Honest negatives

- **Excitation fine structure is approximated**: Sony builds sparse pulse excitations from pulse-position codes derived from a coarse int16 LSF path (FUN_10004b10→FUN_1000a110/FUN_1000c680) plus a per-band pulse allocator (FUN_10004450/FUN_10003d80) and 8-bit-code-indexed value tables (state+0xe0/0xe4/0xe8, row lengths at DAT_10046984); this pass substitutes a pitch-lag impulse/noise train with the exact per-band amplitude envelope. Intelligibility is therefore expected to be partial.
- **Comb post-filter not mirrored** (FUN_1000e4a0 coefficient math); periodicity is instead placed directly in the excitation — overlapping effect, not sample-equivalent.
- **Pitch pulse shaping** (FUN_1000f4e0, 1024-entry ramp tables) and the **A84/A88 runtime windows** (FUN_1000fa90) not mirrored; linear cross-fade ramps substituted.
- **Absolute gain mapping uncalibrated**: the f0-table scale × band rows × pulse-value chain yields unknown absolute levels; a single per-file peak normalization (0.7 FS) is applied instead.
- SP-mode frame-edge RMS discontinuity is inflated by a file-initial transient (frames 1–3); sub-frame continuity within frames is smooth, but no per-subframe continuity metric was computed.
- Validation is plausibility-only: no Sony reference PCM comparison, no listening test, no formant-tracking comparison against a known transcript.
- TRC samples (taxis.dvf, Pinkston) remain excluded — different codec (dsp_trc.dll).

## Next levers

1. Mirror FUN_10004450/FUN_10003d80 (band pulse allocation from the state+0x10c WAV table) + FUN_100060e0 (8-bit code → value rows) to replace the impulse-train approximation — the largest remaining quality gap.
2. Mirror FUN_1000e4a0 (comb taps) and FUN_1000f4e0 (glottal ramps) for sample-accurate periodicity.
3. Wine-based Rosetta: run Sony's own decoder on the same samples and diff PCM to close every remaining approximation (encoder-side Rosetta was already named in F-50).
