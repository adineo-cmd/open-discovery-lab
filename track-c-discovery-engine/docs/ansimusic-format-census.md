# ANSI Music (.mus/.ams) — format census + MIDI converter (F-40, Track C, R-10)

Census date: 2026-11-13. Samples: NOT committed (all in /tmp only).

## Prior art (Rule 0, dated 2026-11-13)

- The PROTOCOL is documented (BBS era, ~1992-1994):
  `artscene.textfiles.com/ansimusic/information/ansimtech.txt` ("ANSI Music -
  The Technical Details"; ESC[M ... CTRL-N wrapper, PLAY-command grammar from
  the Tandy BASIC manual) and `.../dybczak.txt` (Jack Dybczak, author of the
  SMILE viewer; ESC[M + MF/MB/MN/ML/MS prefixes, T tempo, and the
  `ESC[MF Freq;Duration;Cycles;CycleDelay;Variation` SOUND extension with a
  7-octave frequency table). Both read 2026-11-13.
- dexvert `src/format/music/ansiMusic.js` (repo SHA 5d994b4a, read
  2026-11-13): `unsupported = true`, weakMagic, notes "No known converter.
  Maybe easiest would be converting to MIDI?".
- SyncTERM 1.3 (syncterm.bbsdev.net) plays ANSI music live in the terminal
  (2020s bug ticket #176 confirms active use); the r/ANSIart `cat file.mus`
  recipe circulates. Synchronet/SyncTERM `cterm.c` contains a real-time
  player (GitHub code search 2026-11-13, 8 repo hits).
- **Boundary (precise)**: real-time PLAYBACK exists (terminals); the spec is
  public; but NO offline file decoder/converter exists — dexvert's "no known
  converter" note is CURRENT as of 2026-11-13 (web + code search). This
  census closes that gap for the sample corpus.

## Samples

9 files from `artscene.textfiles.com/ansimusic/songs/`: 7 `.mus`
(bandplay, barenec, bethlehm, charge, daisy, mash, musicbox; 150-811 B) +
2 `.ams` (ode2joy, wipeout1; 507-825 B).

## Census findings

- **Container**: ANSI text, CRLF. Each music string is embedded with the
  **concealed-text trick**: `ESC[0m` (reset) + `ESC[<line>;1H` (cursor to a
  screen line) + `ESC[8m` (conceal) + `ESC[M` + PLAY string + ` ` + `0x0E`
  (CTRL-N terminator). Line numbers vary per file (15;1, 24;1). The music is
  written as invisible screen text — transport is the terminal stream.
- **`.ams` = BBS message capture** (same pattern as IGS `.IG` vs `.IGS`,
  F-37): ode2joy.ams opens with a Date/From/To/Subj message header
  ("Ode To Joy by L. Von Beethoven", From: Daniel Liebling, 07 Jun 92);
  the music strings inside are byte-identical in grammar to `.mus`.
- **Event grammar (as documented, verified against samples)**: PLAY strings
  carry `T<tempo>` (default 120), `O<octave>` (0-6, default 4), `L<len>`
  (1-64), note letters A-G with `#`/`+`/`-`, per-note duration suffix
  (`C16`), dots (×1.5), `N<0-84>` absolute (N0 = rest), `P<len>` rest,
  MN/ML/MS articulation.
- **Timing resolution (cracked)**: octave-3 C = middle C = MIDI 60 →
  `midi = 12×(octave+2) + semitone`; quarter note = 60/T seconds; note
  length = (4/L)×(60/T) × dots × mode (MN 7/8, MS 3/4, ML 1); rests always
  full length. N-mapping verified: N1 = MIDI 24, N84 = MIDI 107.

## Decoder (deliverable)

`results/format-re/ansi-music-census/mus2midi.py` — stdlib-only Python:
extracts `ESC[M ... 0x0E` strings from any file (handles .mus and .ams
alike), parses the full PLAY grammar with stream-carried state (terminal
transport semantics: strings play sequentially in file order), emits a
type-0 Standard MIDI File (480 PPQ, tempo metas, channel 0).

Validation (`mus2midi-validation.json`): **9/9 files converted, 0 parse
errors, 730 notes total**. Sanity checks: charge.mus = MIDI 60-67 (C-G —
the cavalry-charge fanfare, correct); wipeout1.ams = 195 notes/6.4 s (fast
surf-rock figure); ode2joy.ams = 31 notes/14.4 s. MIDI outputs written to
/tmp only (regenerate: `python3 mus2midi.py <files>`).

## Cross-reference with IGS .igm (F-37)

Same BBS-era family ("music inside the terminal stream"), different layer:
IGS `.igm` (F-37) is a BINARY MIDI-like varlen event stream after one text
command; ANSI Music is a TEXT grammar (BASIC PLAY) that is MIDI-convertible
at the semantic level. Both now have Track C censuses; the .igm byte-level
grammar remains the open sibling problem.

## Crack verdict

- RESOLVED: protocol → MIDI conversion (grammar, timing arithmetic,
  concealed-text transport, .ams container). dexvert's R-10 "decode tooling
  absent" gap closed for the sampled corpus.
- PARTIAL: Dybczak SOUND extension (`ESC[MF Freq;Dur;Cycles;Delay;Var`) is
  parsed-but-unrendered (needs an SPC-player tone generator, not MIDI).
- NEGATIVE: none material.
