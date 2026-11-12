# Track C — format-RE front v2: dexvert registry harvest + first-look censuses (2026-11-12)

Activates the "legacy voice-recorder formats" item (T-6) of `targets.md` and
widens it into a scored format-RE queue mined from the dexvert format corpus.
Companion raw censuses: `results/format-re/sony-msv-dvf-census.json`,
`results/format-re/proline-pvd-census.json`. No sample files committed
(9 samples fetched to /tmp only).

## Method

- Sources: `Sembiance/dexvert` SUPPORTED.md (4,017 formats) + UNSUPPORTED.md
  (4,025 detected-but-unconverted formats — the spec-gap pool), both at commit
  `b126fe4` (fetched 2026-11-12). Weak-support signals mined from per-format
  notes ("no known converter", "room for improvement", decode-distortion).
- Sample availability verified against `sembiance.com/fileFormatSamples`
  (dexvert's sample mirror; reachable, listings pulled 2026-11-12).
- Rule 0 prior art per top candidate (GitHub code search + WebSearch,
  2026-11-12) before any uniqueness claim. Ratings for queue items 3-12
  carry Sembiance's own notes as novelty proxy and are flagged
  "verify before claim".
- First-look census: hexdump head/tail, printable strings, 1KB-block entropy
  map, cross-file header field alignment (5 PVD files, 4 DVF/MSV files).

## Scored queue (N novelty / F feasibility / V value, max 15)

| # | Target | Ext | N | F | V | Σ | One-line reason | Status |
|---|--------|-----|---|---|---|---|-----------------|--------|
| R-1 | Sony IC voice recorder DVF/MSV (LPEC/TRC) | .dvf .msv | 4 | 5 | 5 | 14 | No open-source LPEC/TRC decoder exists (checked 2026-11-12); PRONOM 2023 submission is ID-only; preservation bodies are stuck with Windows-only Sony tools. 4 samples. | **FIRST-LOOK DONE** |
| R-2 | ProLine Voice Data (Amiga BBS voicemail) | .pvd | 5 | 5 | 3 | 13 | Zero docs/decoders anywhere (TrID sig only); header + PCM body largely cracked in first look below; 8 samples. | **FIRST-LOOK DONE** |
| R-3 | Clarion Database File | .dat | 4 | 5 | 4 | 13 | dexvert: "Did a Google search, couldn't find anything about it"; 49 samples — largest zero-doc corpus found. verify before claim | queue |
| R-4 | Instant Graphics and Sound | .igs .ig .igm | 4 | 4 | 4 | 12 | dexvert 2024 note: "No known converter yet. Seen a recent resurgence in interest in 2024"; 12 samples. verify before claim | queue |
| R-5 | Psion AIK Audio (Psion Series 3 voice) | .aik | 4 | 4 | 4 | 12 | No code-search hits; Psion preservation community active; next step: check psiconv coverage. 3 samples. verify before claim | queue |
| R-6 | Professional Draw Image (Amiga) | .clips | 4 | 4 | 3 | 11 | "No known converter" per dexvert; 10 samples. verify before claim | queue |
| R-7 | Sonic Arranger instrument | (none) | 4 | 3 | 3 | 10 | UNSUPPORTED: "No known converter"; no extension complicates identification. verify before claim | queue |
| R-8 | NTitler Animation (Amiga) | .nt | 4 | 4 | 2 | 10 | "Couldn't locate a converter or extractor"; 8 samples. verify before claim | queue |
| R-9 | DiamondWare Digitized Music | .dwm | 3 | 4 | 3 | 10 | DOS PLAYDWM.EXE is the only player; wrapped-MIDI/OPL decode open. verify before claim | queue |
| R-10 | ANSI Music | .mus | 3 | 4 | 3 | 10 | "No known converter"; scene docs exist at artscene.textfiles.com but decode tooling absent. verify before claim | queue |
| R-11 | Beam Software SIFF Sound | .son | 2 | 4 | 3 | 9 | Weak-support case: JSIT-documented, but ffmpeg decode "often produces very distorted WAVs" — decode-bug RE, not blank-slate. verify before claim | queue |
| R-12 | Creative Music System Intelligent Organ | .org | 3 | 3 | 3 | 9 | "No modern converter known"; referenced converter unlocatable. verify before claim | queue |

Downgraded / rejected: Qualcomm QCP (ffmpeg has both container demux and
QCELP decoder — novelty 1); Digital Speech Standard .dss (ffmpeg demuxer;
Olympus/Philips industry docs — novelty 2); Apple QuickTime Audio (weak notes
but the format family is broadly documented); inrsTelecomAudio,
parrotDigitalSample, microsoftSpeechData, deskMateSound (no samples at the
mirror — feasibility unknown).

## First look #1 — Sony DVF/MSV (R-1, the T-6 anchor)

Why it matters: Sony IC recorders wrote DVF (internal) / MSV (Memory Stick)
files in three codecs (ADPCM, TRC, LPEC). Every conversion route today is
Sony's own Windows software (ICS Converter, Sound Organizer) or commercial
Sound Forge; the LPEC codec has no public decoder anywhere. Preservation
surveys (Obsolete Thor blog, 2023-04-21) document exactly this gap.

Prior art (2026-11-12): PRONOM_Research "Sony Voice Recorders" submission
(2023) = byte-pattern identification only; GitHub code search returns no
decoder; web search confirms no open-source decode path.

Census (4 files: 07011600.MSV, WelcometoPinkston…dvf, budgtele.dvf, taxis.dvf):

- Magic `MS_VOICE` + `00 00 00 50`; codec family at 0x0C (01 01 00 00 =
  LPEC-family, 01 02 00 00 = TRC) matching PRONOM's BOF patterns.
- 0x10 "SONY CORPORATION"; 0x20 = origin string — device model (`ICD-BM1`)
  or codec DLL (`PVoice.dll`, `STVoice.dll`). **Extension is not a reliable
  codec indicator**: budgtele.dvf carries LPEC bytes (`01 01`) — PRONOM's
  "DVF TRC" regex misses it (honest correction to the PRONOM pattern).
- 0x34 big-endian date/time (u16 year, u8 mon, day, h, m): 2007-01-16 16:12,
  2008-01-29 20:39, 2006-02-06 13:02 — first two match filenames; taxis.dvf
  has 0xFF = unset. Forensic hook: DVF also embeds free-text annotations
  (`Jane Ann Knowles` recovered from strings).
- **Structural finding**: 0x3C BE u16 codec submode (42/44/48 per codec
  variant), 0x40 BE u32 = bitrate bits/s (16000 / 19200 / 6000), and
  0x44 BE u32 = **exactly bitrate/8** in all three decoded files (2000,
  2400, 750 bytes/s). Not previously documented publicly.
- 0x50: 8-byte-stride tag/size table (tags 01-0E seen), then padding; audio
  entropy from ~1-2KB at 7.7-7.9 bits/byte (compressed bitstream, no
  byte-level structure).

Open for full RE: pin frame size from the bitrate field, decode the 0x50
TOC, and the LPEC bitstream itself — the actual prize.

## First look #2 — ProLine Voice Data (R-2)

Why it matters: voice-mail clips of the Amiga ProLine BBS. dexvert detects
but skips them ("only 16 unique files on discmaster… unlikely to be sampled
audio"); no doc or decoder exists anywhere. The census refutes Sembiance's
doubt — these are real sampled audio.

Census (5 files, all headers identical in shape):

- 0x00: Pascal length-prefix `0x12` + `"Proline Voice File"` (18 chars);
  0x13: version `01`; 0x14-0x16: 24-bit LE payload length == filesize−24
  in 5/5 files.
- 0x17: constant `00 AD` (173) in every file — candidate: Amiga Paula
  audio period (3546895/173 ≈ 20502 Hz PAL, 3579545/173 ≈ 20685 Hz NTSC).
  UNCONFIRMED.
- 0x19: unsigned 8-bit PCM, silence floor 0x7F (GELD/JUBEL open with 0x7F
  runs); heavy consecutive duplicates = smooth/oversampled waveform — the
  "each sample stored twice" first impression was self-corrected (KMERA has
  non-doubled transitions `80 7f 7e`).
- Honest negative: BOMB.PVD body begins with ASCII "RIFF" + implausible
  length — judged audio-data false positive, flagged for one future look.
- Rate check next: resample at ~20.5 kHz and listen; clip lengths at that
  rate (~0.5 s for JUBEL) fit BBS event sounds.

## Next moves

1. Full RE of PVD (small, tractable — likely finishable: header + raw PCM,
   only sample-rate + 2 bytes unexplained). Candidate lab "format decoded"
   claim pending listening tests.
2. Sony DVF/MSV frame census: use 0x44 bytes/s to derive frame geometry;
   TOC decode; then decide if LPEC bitstream RE is tractable in-house.
3. R-3 Clarion .dat (49 samples, zero docs) as the next harvest candidate.
4. Rule-0 verify each queued item before claiming uniqueness in any writeup.

## Instrument provenance

- dexvert SUPPORTED.md / UNSUPPORTED.md @ b126fe4 (2026-11-12 fetch)
- sembiance.com/fileFormatSamples listings (2026-11-12)
- GitHub code search: "proline pvd voice", "sony dvf voice", "LPEC sony
  voice", "psion aik audio" (2026-11-12)
- WebSearch: Sony DVF/MSV converter landscape; ProLine PVD (2026-11-12)
- PRONOM_Research Submissions/Complete/Sony Voice Recorders (2023 submission,
  read 2026-11-12)
- Just Solve It wiki unreachable from this network (known constraint) — all
  JSIT references here are secondhand via dexvert links/digipres.org.
