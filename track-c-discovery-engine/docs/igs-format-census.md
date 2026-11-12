# Instant Graphics and Sound (.igs/.ig/.igm) — format census (F-37, Track C, R-4)

Census date: 2026-11-12. Samples: NOT committed (all in /tmp only).

## Prior art (Rule 0, dated 2026-11-12)

- dexvert `src/format/image/instantGraphicsAndSound.js` (repo SHA b126fe4f, checked 2026-11-12): `unsupported = true`, notes `"No known converter yet. Seen a recent resurgence in interest in 2024"`. Detection: weakMagic + TEXT_MAGIC + idCheck = bytes `G#` (0x47 0x23) in first 1KB. ext `.igs .ig .igm`. Only 46 unique files on discmaster.
- GitHub code search 2026-11-12 (`instantGraphicsAndSound repo:Sembiance/dexvert`): 1 hit (the module above). No public decoder/README/spec found via web search 2026-11-12 either.
- Community interest verified: multi-part history series on Reddit r/bbs ("A look at the legacy of IGS", ~Oct 2024) and r/vintagecomputing ("Years before RIPscrip, there was 'IGS'", Sept 2024) — this is the "resurgence in 2024" dexvert cites. No tooling came out of it as of 2026-11-12.
- VERDICT: dexvert's "no known converter" note is CURRENT as of 2026-11-12. Prior art = identification artifacts only (dexvert detection, TrID-style signature lists). No spec found. This census is the first public structural write-up we located.

## Samples

12 files from `https://sembiance.com/fileFormatSamples/image/instantGraphicsAndSound/` (dexvert-samples GitHub repo 404s for our token; mirror used). Sizes 1135–21795 B. Dates in mirror listing: 1985 (CUBES.IG, DEVO3.IG), 1993 (most .IGS), 2025-01-02 (fifth.igm — recent upload, matching the 2024+ interest).

## Census findings

- **Container**: plain text, CRLF line endings. Two kinds of lines: BBS message text and command lines. Command lines are prefixed `G#` (the dexvert idCheck bytes) in most files; CLRDEMO.IGS and the `TYPE*.IGS` set carry commands without the `G#` prefix (older/different protocol revision — command grammar identical).
- **Command grammar (cracked)**: `letter>args` records separated by `:`; a trailing `_` at end of line = wrapped continuation (join with next line); `@` terminates `W>` text payloads. `letter>args` matches every stream segment across all 12 samples.
- **Coordinate space (cracked by arithmetic)**: Atari ST screen **640 x 200**. Measured across 12 samples: max x = 639 (B> boxes), max y = 199 (B/CUBES.IG), **0 coordinate violations in 1293 numeric args** checked by the decoder.
- **.IG vs .IGS (cracked by pair diff)**: XNET_LST.IG (21795 B) and XNET_LST.IGS (21585 B) have byte-identical command streams (1432 commands each, same xmax/ymax); the .IG variant simply has a 9-line BBS message header (Conf/Msg#/To/From/Subj) prepended. `.IG` = message capture, `.IGS` = bare protocol stream.
- **Command inventory** (observed letters; semantics where inferred): `I>0` init; `s>0` / `k>1` mode/key-color toggles; `C>pal,color` pen color; `B>x1,y1,x2,y2,c` box; `L>x1,y1,x2,y2` line (polyline chains repeat vertices); `D>x,y` line-to from current point; `W>x,y,text@` write text (BBS names visible: "The LONDON SMOG BBS", "IG SUPPORT BOARD"); `T>1,1,1` text setup; `F>x,y` fill; `S>r,g,b` ?; `E>0,8,0` ?; `A>`, `X>`, `b>`, `t>`, `M>`, `G>1,3,0,0,639,199` (screen-window?), `H>`, `J>x,y,...`, `O>`, `P>` — present but semantics unverified (honest negative).
- **`&>` macro command (partial)**: `&>n,...,subcmd-letter,vals,...,x,...` — repeat/macro construct with `x` placeholder tokens (e.g. `&>0,639,4,0,L,4,320,0,x,199`); grammar not fully resolved.
- **Music layer**: `n>inst,slot,vol,pitch,0,1` text note events (DEVO3.IG: 144 events, inst ∈ {1,8}, slot cycles 0/1/2, vol = 15, pitch 38..96 — MIDI-range pitches); `q>n` tempo-like. `fifth.igm` (.igm, 13.4 KB): single `G#N>1,9998,` command followed by a **binary variable-length MIDI-like event stream** (13,416 B): most common non-zero bytes 0x90–0x94 (note-on, channels 0–4 shape), pitch bytes cluster 36–79 (MIDI note range), velocity-like bytes 0–127. Full event grammar NOT resolved in this timebox (honest negative).
- **CLRDEMO.IGS**: full BBS session capture — ANSI login/menu text interleaved with IG command lines (205 non-ASCII bytes = ESC sequences); shows the in-the-wild transport (terminal stream, not a standalone file format).

## Crack verdict

- RESOLVED: container type (text/CRLF/G# lines), command-record grammar, wrap convention, text terminator, 640x200 coordinate space, .IG-vs-.IGS relationship.
- PARTIAL: music event semantics (text form mapped to ranges; binary .igm stream only fingerprinted); `&>` macro grammar; semantics of ~14 of 25 command letters.
- NEGATIVE: no public decoder found anywhere as of 2026-11-12; no sound renderer.

## Decoder

`results/format-re/igs-census/igs_decode.py` (stdlib Python): tokenizes command streams, unwraps `_` continuations, histograms commands, validates x<=639/y<=199, extracts `W>` text payloads and `n>` events; `--svg` renders L/D polylines to SVG as proof-of-decode (generated `igs-census/shut_med-render.svg` from SHUT_MED.IGS: 780 line elements, no coordinates outside the 640x200 viewport).

Validation (`igs-census/igs-validation.json`): 12/12 samples tokenized; 0 coordinate violations; XNET_LST .IG/.IGS pair parses identically (1432 commands each).

## Next steps

- Map remaining command letters against an Atari ST VDI opcode table (L/B/D/W/C already match GEM VDI drawing primitives).
- Crack `&>` by diffing repeated structures inside one file; crack `.igm` event grammar (candidates: 1 status byte + varlen delta like SMUS/MIDI).
- Sound: the `n>` text events are already convertible to MIDI pitch/volume/duration candidates without knowing exact timing.
