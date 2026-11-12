# Sonic Arranger standalone instrument (SASI) — format census (F-39, Track C, R-7)

Census date: 2026-11-12. Samples: NOT committed (36 instrument files in /tmp only).

## Prior art (Rule 0, dated 2026-11-12)

- dexvert `src/format/audio/sonicArrangerInstrument.js` (SHA b126fe4f, checked
  2026-11-12): `unsupported = true`, `fileSize = 672`, notes **"No known
  converter"**, 43 unique files on discmaster, no extension.
- TrID def `sa-inst.trid.xml` (digipres.github.io mirror, checked 2026-11-12):
  magic ASCII `SASI` at BOF, no ext, generated from 47 files, def dated
  2018-04-19 (Marco Pontello). Wikidata Q105852416 mirrors the signature.
- The *module* format is a different story: dexvert SUPPORTS "Sonic Arrange
  Module" (.sa) via uade123, and open implementations exist — UADE
  amifilemagic.c (magic `SOARV1.0`, packed `SA-P`) and the nuade replayer
  (`emoon/nuade players/sonicarranger/sonic_arranger.c`, checked 2026-11-12)
  which fully parses unpacked modules: `SOARV1.0` + chunks STBL/OVTB/NTBL/
  INST/SD8B/(sample data)/SYWT/SYAR/SYAF, and compiled 68k `.pc` modules with
  an offsets table + `deadbeef` trailer. **The standalone SASI instrument
  file is not handled by UADE/nuade or anything else we could find.**
- DieMusic spec DB (via horsicq/xxfclib stub, checked 2026-11-12) catalogs
  "BrainTrace Design/MEDIA Verlags Sonic Arranger synth instrument".
- Provenance with dates: the Aminet CD-12 index (AmigaTextFiles/docs) lists
  `Sonic_ArrangI.lha` ("Sonic Arranger instruments", mus/misc) and
  `SonicArrangTun.lha` ("Short mods with player source"); the shipped
  `Sonic_Arranger_Replay_Ex.s` is "(c) by BrainTrace Design / Carsten
  Schlote, Lich, Germany" (files dated 1990–1992, CD Jun 1996).

VERDICT: dexvert's "No known converter" is CURRENT as of 2026-11-12. Prior
art for the standalone instrument = identification artifacts only. This
census is, to our knowledge, the first public structural write-up of SASI.

## Samples — recovery note (useful method)

sembiance.com mirror has **no** sonicArrangerInstrument dir; the
dexvert-samples repo 404s for our token; Aminet mirrors + exotica +
fileformats.archiveteam.org were unreachable from this network. Route that
worked: archive.org item **`aminet-12`** (Aminet CD-ROM #12, Jun 1996) holds
a 669 MB ISO; we range-read the ISO9660 directory tree over HTTP (root →
AMINET → MUS → MISC), pulled `SONIC_ARRANGI.LHA` (9.7 KB) + READMEs +
`SONICARRANGTUN.LHA`, and unpacked the LHa (python `lhafile`, pip-installed
to /tmp) → **36 instrument files, all exactly 672 bytes** (dexvert's
`fileSize=672` corroborated; the 43-file discmaster corpus is a superset).

## Census findings

- **Container (resolved, 36/36)**: `672 = 8 + 152 + 4*128`:
  - 0x00: magic `"SASI\0\0\0\0"` (8 bytes);
  - 0x08: **152-byte instrument record whose byte layout is identical to the
    per-instrument `INST` entry inside SA modules** — cross-validated by
    parsing a real unpacked module (`time to death.sa`, `SOARV1.0`, 4
    records x 152 B) with the same field map: 30-byte NUL-padded name at
    record offset 122 (= file offset 130, all 36 files), volume 0–64 at
    +16, waveform fields at +0..6, vibrato/AMF/ADSR/effect u16 fields, 3
    arpeggio records {u8 len, u8 repeat, 14 x i8} at +74..121;
  - 0xA0: four 128-byte tables (512 B).
- **Observed field ranges (measured, 36/36)**: type = 1 (synth) everywhere;
  waveform_length ∈ {1,16,32,64}; volume 30..64; vibrato_delay 0..255 or
  65535 (off); effect args 0..127 plus 65408 (0xFF80). Names match file
  names (Acomp Bass, Attack String, Cool Bell, ... some with editor's
  `--` suffix aliases).
- **Table roles**: blk0 @160 = waveform, signed 8-bit (Light_Sine is a
  textbook sine; snare = noise; ramp for bass) — nonzero count correlates
  with waveform_length. blk1 @288 = ADSR/amplitude table, values 0..64
  (Amiga volume scale), present in all 36. blk2 @416 = AMF-style modulation
  table (63-centered sine curves; sparse — ~5/36 nonzero). blk3 @544 =
  second waveform-like signed table (square/noise shapes) — role tentative:
  candidates are synth-effect waveform or morph target (cf. `SineMorf`).
- **`.sadir` companion** (from the same archive): stride-44 entries =
  42-byte NUL-padded name + u16 BE size (`0x02A0` = 672); lists instruments
  and `.pc` modules — the SA file directory format.

## Crack verdict

- RESOLVED: 672-byte container identity; instrument record = module INST
  entry layout (name slot, volume scale, arpeggio stride cross-validated
  against a real module); blk0 waveform / blk1 0–64 envelope roles.
- PARTIAL: blk2 (AMF?) and blk3 (second waveform?) semantics; mapping of the
  4 tables onto the module's SYWT/SYAR/SYAF chunk family.
- NEGATIVE: no standalone-SASI decoder existed before this census (verified
  2026-11-12); player-accurate synth semantics live in the module RE
  (nuade), not in the container.

## Parser

`results/format-re/sonic-arranger-census/sa_instrument_probe.py` (stdlib
Python): parses SASI files to a full field dump (also `--json`), and
cross-checks instrument records from an unpacked module (`--module
FILE.sa`, STBL/OVTB/NTBL walk). Validation: 36/36 SASI valid; module
crosscheck 4/4 records x 152 B.

## Next steps

- Diff an instrument exported from a module against a standalone SASI of the
  same patch to pin blk2/blk3 onto SYAR/SYAF semantics.
- Hunt MEDIA Verlag / MediaPoint manuals (1992) for the official save format.
- A SASI→WAV renderer is now feasible: waveform + envelope + effect fields
  are all in hand; nuade's synth code is the reference.
