# Psion Series 3 AIK Audio (AICASoundFile) — format census (F-39, Track C, R-5)

Census date: 2026-11-12. Samples: NOT committed (3 .aik files in /tmp only).

## Prior art (Rule 0, dated 2026-11-12)

- dexvert `src/format/audio/psionAIKAudio.js` (SHA b126fe4f, checked 2026-11-12):
  `unsupported = true`, comment "only 3 unique files on discmaster"; magic string
  "Psion serie 3 AICA Sound Compressor audio" (TrID wording); ext `.aik`.
- TrID2 database (Papyrus7914/TrId2-file-type-identifier, checked 2026-11-12):
  identification-only — BOF ASCII `AICASoundFile**`; description field names the
  author: **"Audio compressor by Marco Aicardi"** — so AICA = Aicardi's
  compressor, not the Dreamcast chip despite the acronym.
- **psiconv coverage check (the R-5 open question): AIK is NOT covered.**
  psiconv (kianryan/psiconv fork of Frodo Looijaard's original, checked
  2026-11-12) handles Word/TextEd/Sketch/MBM/Sheet/Database (Series 5-era
  record formats); Series 3 sound files are absent. AIK also does not use the
  generic Psion record wrapper — it is a standalone string-magic format.
- GitHub code search `AICASoundFile` (2026-11-12): 2 hits, both identification
  artifacts (the TrId2 yaml; theseus-rs/file-type wikidata-105854924 signature
  stub whose "test file" is just the 15-byte signature). **No decoder, no spec
  anywhere.** dexvert's "no code-search hits" note is CURRENT.

VERDICT: blank-slate confirmed as of 2026-11-12. This census is the first
public structural write-up we located.

## Samples

3 files from `sembiance.com/fileFormatSamples/audio/psionAIKAudio/` (dexvert
mirror): TETRIS_2.AIK, TETRIS_3.AIK (15,392 B each — different audio, same
length), TETRIS_4.AIK (7,712 B). All Psion "Tetris" game sounds, 1990s.

## Census findings

- **Magic (resolved)**: 0x00: Pascal-style `0x0F` + `"AICASoundFile**"` (15
  chars) + `0x00` = self-describing 16-byte block.
- **Size rule (resolved, 3/3)**: u16 BE at 0x12 = N, and
  `filesize == 32 + N*128` exactly (N = 120, 120, 60). The body is N fixed
  128-byte frames after a 32-byte header (16 magic + 16 info).
- **Info block (partial)**: 0x10 `0x0F` (candidate: magic strlen again),
  0x11 `0x10` (candidate: header size 16), 0x12-0x13 N (BE u16), 0x14-0x17
  zero, 0x18 `0x01`, 0x19-0x1F zero.
- **Body packing (partial)**: nibble-aligned 4-bit codes, 2 per byte — hi/lo
  nibble histograms are near-identical per file, and file tails are pure
  `0x55` (silence = code 5). At 2 samples/byte the body holds N*256 samples,
  giving **4096 Hz if N counts 1/16 s** or **8192 Hz if N counts 1/32 s**
  (EPOC16 tick) — both exact for all files; unit unconfirmed.
- **Code alphabet (honest negative)**: nibble **2 never occurs** in any
  sample (61,440 nibbles scanned); codes 4/10/12/13 are rare; peaks at 3, 11,
  8, 0. This is a codebook/compander mapping, not linear PCM. The amplitude
  mapping is the unsolved core.
- **Entropy**: 4.9–6.8 bits/byte per 1 KB block; last KB of TETRIS_4 = 0.49
  (pure silence pad). No embedded app metadata or strings beyond the magic.

## Crack verdict

- RESOLVED: magic block, 32-byte header shape, N x 128-byte frame arithmetic,
  silence code (5), nibble packing.
- PARTIAL: rate candidates 4096/8192 Hz (N unit); info-block field meanings.
- NEGATIVE: nibble→amplitude codebook (the actual codec).

## Parser

`results/format-re/psion-aik-census/aik_decode.py` (stdlib Python): validates
magic + size rule, prints header fields, nibble histogram (flags the missing
code 2), tail-silence check; `--wav OUT RATE` emits a stereo WAV with the two
candidate mappings (signed-nibble vs offset-binary) for A/B listening tests —
explicitly an unverified codec probe, run locally (artifact not committed).

Validation: 3/3 files pass magic + `32 + N*128` + no-code-2.

## Next steps

- Get a known-content AIK (Psion alarm tone) and match waveform periods to
  pin the codebook and rate.
- EPOC16 ROM/SDK dig for the "AICA" (Marco Aicardi) compressor API docs.
- If the codec proves to be per-frame codebook VQ, the 128-byte frame is a
  natural 256-sample superframe at the derived rates — test that framing.
