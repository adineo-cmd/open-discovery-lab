# Psion AIK Audio (.aik) nibble codebook - decode attempt (F-44-or-next-free)

Track C, R-5 follow-up to F-39 (container crack stands; this doc attacks the named open
item: the nibble->amplitude codebook of the AICA sound compressor).

Date: 2026-11-13. Samples re-fetched to /tmp from
`sembiance.com/fileFormatSamples/audio/psionAIKAudio/` (TETRIS_2/3/4.AIK, sizes 15392/15392/7712,
size rule 32 + N*128 re-verified on fetch). WAV probes in /tmp only, not committed.

## Claim

The AIK body is **unit-step signed-magnitude DPCM**, not IMA/OKI ADPCM and not direct
companded PCM:

- nibble = sign (bit 3) + magnitude index (bits 2-0)
- sample update: `x[n] = clip(x[n-1] +- L[mag], -128, 127)` (8-bit signed output)
- **silence anchor: codes 5 and 13 (mag 5, both signs) have L = 0** (zero diff =
  hold), matching the observed pure-0x55 tails; codes 6/14 are a second (near-)hold
  pair in the best-fit table - four hold codes fits square-wave chiptune sustained notes
- best-fit level table: **L[mag 0..7] = [2, 1, 7, 4, 6, 0, 0, 3]**
- predictor is per-256-nibble-frame reset in the best bounded/clip-free decode

Confidence: codec FAMILY high (three independent sharp statistics, all 3 files);
exact small-level assignment of the table medium-low (see residual ambiguity).

## Hypotheses tested, in order

1. **IMA/DVI ADPCM (prime hypothesis, standard public mapping)** - NEGATIVE.
   Repeated code 5 = +1.5*step with index +4/sample: the 0x55 silence tails
   (313-487 bytes) decode to tail RMS 27000-30700 of 32767 full scale in all 3 files.
   Silence must be a zero code; IMA has none. (16x code 5 probe: [8,22,44,74,120,188,288,434]...)
2. **OKI/Dialogic (VOX) ADPCM** - NEGATIVE. Same contradiction, faster ramp
   (16x code 5: [2816, 6864, 12848, 21648, 32752...] saturates).
3. **Direct companded PCM** (nibble = amplitude, sign = bit3, L[5] = 0) - NEGATIVE
   (weaker family). Best of 5040 level permutations: SFM only -10.5 dB vs -20..-23 dB
   for the DPCM family. Also: TETRIS_2's opener is mostly hold codes with isolated
   +-1 blips (codes 4/12) - as direct PCM those would be isolated impulse clicks in
   silence; as DPCM they are natural near-silence +-1 tracking steps.
4. **Unit-step signed-magnitude DPCM, L[5] = 0** - POSITIVE. Empirical codebook
   derivation: exhaustive search of all 5040 permutations of levels over mags
   {0,1,2,3,4,6,7} (L[5]=0 fixed by the silence anchor), scored by (a) boundedness of
   the per-frame decode (music frames only), (b) spectral flatness (tonality), (c)
   pitch concentration of per-frame f0 tracks. A narrow perm family reaches in-range
   0.995-0.996 on ALL 3 files simultaneously (random-walk baseline ~0.5); the winner
   decodes to tonal audio (SFM -20..-23 dB), RMS 22-49, zero clipping.
5. **Full-file predictor carry** - NEGATIVE as decode, with a metric lesson: the
   no-clip cumsum never stays bounded (best 0.53); clip-carry decode drifts
   monotonically into the -128 rail (RMS 105-114, clip 6-15%, range capped at
   -128..+14). Rail-clipping manufactures harmonics that inflate SFM (-43 dB) - an
   objective-function artifact we caught and discarded.
6. **Per-frame 1-byte predictor seed** (frame = seed byte + 254 nibbles; 127*2 = 254
   fits) - NEGATIVE: silence frames decode to the seed DC (sil_rms 85; 0xdd = -35),
   contradicting silence = zero.
7. **Adaptive-step variants** (IMA index table on mag / on level / level-3 law with
   the count-ordered candidate table) - all diverge (in-range 0.000-0.003).

## Cross-checks that pin the structure

- **Mirror-pair statistics**: bit3 sign flips have near-equal nibble counts
  (TETRIS_2: 0/8 = 3932/3952, 1/9 = 2372/2306, 3/11 = 5372/5207, 6/14 = 1326/1387,
  7/15 = 720/811) - sign-bit structure confirmed. Pairs (5,13) and (2,10) break
  symmetry, explained by their special roles (zero code; one-sided max level).
- **Code 2 = 0 occurrences in 61,440 nibbles** while mirror code 10 occurs 1015
  times: consistent with L[2] = max level (+7) that the content saturates against
  on the negative side only.
- **Pitch structure**: decoded frames give stable melodic f0 tracks (descending
  sequences over lags 5-30 samples); at 8192 Hz several near-exact equal-tempered
  fits (292.6 Hz vs D4 293.7, 390.1 vs G4 392, 327.7 vs E4 329.6).

## Residual ambiguity / honest negatives

- Exact assignment of levels {0..3} among mags {0,1,7} and whether L[3] = 3 or 4,
  L[4] = 5 or 6: top candidates within 0.5 dB SFM. Needs a known-content AIK
  (e.g. a Series 3 alarm tone with known waveform) to pin.
- Frame-boundary discontinuities in the per-frame-reset decode (mean jump 26-70 vs
  median sample step 2) are unexplained - some per-frame state mechanism (seed,
  carried-with-clip reference, or intra-frame ordering) is not fully recovered.
- **Rate 4096 vs 8192 Hz not arbitrated**: pitch-ratio structure is rate-invariant,
  so audio statistics alone cannot choose. 8192 Hz remains favored only by the
  census N-unit hypothesis (frame = 1/32 s EPOC16 tick). The decoder takes the rate
  as a parameter; WAV probes for both rates are in /tmp.
- Prior art re-check (2026-11-13): WebSearch for Marco Aicardi / AICA compressor
  documentation - nothing public found; F-39's verdict stands (identification
  artifacts only: TrID2 yaml, wikidata Q105854924, dexvert unsupported).

## Artifacts

- Decoder: `results/format-re/psion-aik-census/psion_aik_decode.py` (stdlib-only;
  container validation + nibble unpack + unit-step signed-magnitude DPCM decode +
  WAV out; rate parameter default 8192).
- Machine results: `results/format-re/psion-aik-census/psion-aik-decode.json`.
- Decoded WAVs: /tmp only (TETRIS_2/3/4 at 4096 and 8192 Hz).
