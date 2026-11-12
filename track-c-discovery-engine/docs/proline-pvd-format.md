# ProLine Voice Data (.pvd) — full format spec (first public)

Track C, R-2 of the format-RE queue (`results/format-re-v2.md`). Extends the
F-34 first-look census (`results/format-re/proline-pvd-census.json`) to a
complete byte-level spec and the format's first working decoder.

**Status: DECODED.** All 5 available samples decode to valid 16-bit WAV
(`results/pvd-validation.json`, all checks pass). Two items remain
hypothesis-grade and are marked: the meaning of byte 0x17 (=0xAD) and the
absolute sample rate (they are the same question). No listening test was
possible in-session; the rate decision is evidence-ranked, not proven.

## Byte-level layout (verified 5/5 samples, 2026-11-12)

| Offset | Size | Type | Field | Observed |
|--------|------|------|-------|----------|
| 0x00 | 1 | u8 | Pascal string length | `0x12` (18) in 5/5 |
| 0x01 | 18 | ASCII | Magic | `Proline Voice File` in 5/5 |
| 0x13 | 1 | u8 | Version | `0x01` in 5/5 |
| 0x14 | 3 | u24 LE | Payload length | == filesize − 24 in 5/5 |
| 0x17 | 1 | u8 | **Mystery constant** | `0xAD` (173) in 5/5 |
| 0x18 | 1 | u8 | Payload start delimiter | `0x00` in 5/5 |
| 0x19 | N−2 | u8 PCM | **Audio: unsigned 8-bit mono PCM** | silence floor `0x7F` |
| last | 1 | u8 | Payload end delimiter | `0x00` in 5/5 |

Corrections/extensions to the F-34 census (self-corrections in place):

- The census placed the body at "0x19" and read `0x00AD` as a u16 at 0x17.
  Arithmetic forces the reading above: payload = filesize − 24 must start
  at 0x18, so **0x17 is a single byte (0xAD)** and the `0x00` the census
  grouped with it is the payload's **first byte** — and the last payload
  byte is also `0x00`. All 5 samples open and close their payload with a
  lone `0x00` surrounded by silence-floor/normal audio: structural
  delimiters, not audio (a full-swing −128 sample adjacent to pure silence
  at both boundaries of every file is not a plausible recording artifact).
  Alternative reading — 0x17-0x18 is a u16 LE Paula period `0x00AD` and the
  trailing `0x00` is a 1-byte file terminator — yields the **identical
  audio bytes**; both are documented in the decoder (`--keep-delimiters`
  keeps the raw payload).
- The census's "JUBEL = 10146 samples / ~0.5 s" used the abandoned
  doubling hypothesis; the actual audio is 20290 bytes = **0.99 s at the
  recommended rate**.

## Audio encoding

Unsigned 8-bit linear PCM, one sample per byte, mono, no chunking or
alignment structures — a flat byte stream inside the delimiters.

- **Silence floor = 0x7F** (127): GELD and JUBEL open and close with runs
  of `0x7F` (57% of GELD is floor); recordings idle at 127, one LSB below
  the unsigned midpoint 128 (typical real-ADC half-LSB bias).
- Conversion to 16-bit WAV (decoder default): `s16 = (byte − 128) × 256`
  (standard unsigned→signed scaling). The 0x7F floor then maps to −256 =
  −42.1 dBFS DC (inaudible as DC; `--zero-floor` maps `(byte − 127) × 257`
  so the floor is exactly 0). Verified: every output sample equals
  `(byte−128)×256` exactly; nothing leaves int16 range; wave-module
  round-trip exact.
- Duration = audio bytes / rate. Payload length makes files
  self-delimiting.

## The 0x00AD question and the sample rate (UNRESOLVED-BY-LISTENING)

Byte 0x17 = 173 is constant across all 5 files. Ranked hypotheses:

1. **Amiga Paula audio period, 173 → ~20.5 kHz (RECOMMENDED default).**
   PAL clock 3,546,895 / 173 = 20,501.7 Hz; NTSC 3,579,545 / 173 = 20,685.0.
   An Amiga-native voice format storing a fixed recording period is exactly
   what this byte looks like; it sits in the header where a hardware
   parameter belongs, and a fixed period across recordings implies one
   global rate for the software — consistent with 5/5 constancy. Duration
   at 20.5 kHz: 0.04–0.99 s — plausible BBS UI event sounds.
2. **8 kHz.** No evidence: no header byte points to it; the clips become
   0.10–2.54 s (long for UI sounds); and under 8 kHz, KMERA/GELD spectral
   support runs to their Nyquist with no telephony-style anti-alias cutoff
   above 3.4 kHz — unusual for genuine 8 kHz captures.
3. **11,025 Hz stereo** — a real trap. The audio of BOMB.PVD **embeds a
   mostly-intact WAVE header**: `RIFF....WAVEfmt ` with a fully consistent
   fmt (PCM, 2 ch, 11025 Hz, byte-rate 22050, align 2, 8-bit) — but the
   RIFF/data size fields (46,636/46,600 B) describe a 2.11 s file while
   only 7,689 PCM bytes are present: **BOMB is a truncated WAV import**,
   not the format speaking. De-interleave confirms: BOMB and DIA carry
   interleaved L≈R stereo (channel corr 0.999, 80-82% exactly-equal
   frames), while KMERA/GELD/JUBEL are native mono streams (pairing 13-44%,
   KMERA odd/even corr 0.23). So 11025-stereo describes two import
   artifacts, not the format. Decoding BOMB as mono at 20502 produces a
   rate-doubled rendition; `--mode embedded` decodes it at its declared
   11025 Hz stereo (3866 frames = 0.351 s of the original 2.11 s).

Why content statistics cannot settle it: the clips are **broadband sound
effects**, not speech (filenames are German: KMERA = Kamera, GELD = money,
JUBEL = cheering, BOMB, DIA). Spectral support extends to ~Nyquist at any
hypothesized rate (99.5%-energy point 0.29–0.49 cycles/sample — consistent
with unfiltered lo-fi capture), so aliasing/formant analysis has no lever.
The Paula-period hypothesis wins on format-internal evidence and is the
decoder default; `--rate` makes every alternative reproducible.

## Decoder

`results/format-re/pvd-decoder/pvd_decode.py` — standalone, Python 3
stdlib only, ~260 lines, tested on all 5 samples.

    python3 pvd_decode.py INPUT.pvd [-o OUT.wav] [--rate HZ] [--ntsc]
                          [--mode raw|embedded] [--stereo] [--zero-floor]
                          [--keep-delimiters] [--no-wav] [--json]

Default: 20502 Hz mono 16-bit WAV. Validates magic, version, and the
payload-length==filesize−24 invariant (raises on violation; truncation and
bad-magic negative-tested). Detects the 0x00 delimiters, the embedded
RIFF (reports declared-vs-present sizes and truncation), and the stereo
pairing fraction. `--mode embedded` honours BOMB's embedded WAVE header.

## dexvert comparison (prior art)

Sembiance/dexvert `src/format/audio/prolineVoice.js` (SHA 584cba02,
fetched 2026-11-12) is **detection only**: `unsupported = true`, with the
comment *"only 16 unique files on discmaster, small file size, unlikely to
be sampled audio"*. It performs no conversion whatsoever. The census
already refuted the "not sampled audio" doubt; this work goes further:

| | dexvert | this work |
|---|---|---|
| Identify .pvd | yes (magic + ext) | yes (validated parse) |
| Convert to WAV | **no** (`unsupported`) | **yes**, all 5 samples, validated |
| Format spec | none | full byte-level spec |
| Payload-length invariant | unused | verified 5/5, enforced |
| 0x00 delimiters | unknown | found, handled |
| Rate question | unknown | Paula-period hypothesis + alternatives ranked, all reproducible |
| Stereo WAV-import case | unknown | detected (BOMB/DIA), handled via --mode embedded |

## "First public standalone decoder" claim + Rule 0 check

Queries run 2026-11-12 (F-34 also searched; re-checked this session):
GitHub code search `Proline Voice File` / `proline pvd voice`; web search
for ProLine BBS voice-mail format documentation. All hits are
identification-only artifacts: dexvert's detector (above), TrID
`audio-pvd.trid.xml`, file-signature lists. No decoder, no spec, no RE
write-up found anywhere. Claim: **first public standalone decoder and
first public format spec for .pvd** — with the honest caveat that the
sample-rate value is hypothesis-grade (see above) and that a third party
could have an unpublished private decoder we cannot rule out.

## Provenance

- Samples: sembiance.com/fileFormatSamples/audio/prolineVoice/ — DIA.PVD
  (810 B), KMERA.PVD (7,053), BOMB.PVD (7,759), GELD.PVD (20,184),
  JUBEL.PVD (20,316); fetched to /tmp 2026-11-12, sizes match the F-34
  census exactly. **No samples or WAVs committed** (regenerable via the
  committed decoder).
- dexvert prolineVoice.js @ Sembiance/dexvert commit b126fe4 (SHA 584cba02).
- Analysis: numpy 2.5.4 for spectral evidence (validation-side only — the
  committed decoder is pure stdlib); decoder + validation runs under
  Python 3.12.3.
- Negative results: rate NOT resolvable from content statistics alone
  (broadband-effect reason above); BOMB declared-vs-present size mismatch
  documented, not silently fixed.
