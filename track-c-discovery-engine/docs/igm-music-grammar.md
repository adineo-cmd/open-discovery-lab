# IGS .igm binary music-stream grammar — cracked (F-41, Track C)

Census date: 2026-11-13. Sibling of `igs-format-census.md` (F-37) and `ansimusic-format-census.md` (F-40).
Samples: NOT committed (in /tmp only). One .igm in corpus: `fifth.igm` (13,428 B, sembiance mirror, uploaded 2025-01).

## Claim

The IGS `.igm` binary music layer is a **MIDI-like chunked event stream** and its note-record grammar is:

```
note event (6 bytes, big-endian):
  [status] [f1] [pitch] [f3] [dur] [delta]
  status = 0x90..0x94  (low nibble = channel; all real notes observed on 0x90)
  f1     = flag 0/1    (unresolved; NOT a voice id — differs between a note's
                        attack and its release)
  pitch  = raw MIDI note number 36..87 (0 = silence marker)
  f3     = flag 0/1    (unresolved)
  dur    = 0x57 (87) on every note attack, 0x00 on every release
  delta  = ticks until the next event (0..255 observed)
```

Container: one or more `N>1,<len>,` text headers, each followed by exactly `<len>`
bytes of event stream; chunks concatenate into ONE continuous stream. A 6-byte
record may straddle a chunk boundary — the next `N>` header is spliced between
its halves, and the straddled record travels as a compressed 4-byte form
`[status, f1, dur, delta]` (pitch/f3 inherited). File ends with `0xFE 0x00`.

Verdict: **RESOLVED (structure) / PARTIAL (flag + control semantics)**. Believed
first public decode of the IGS music layer (dexvert still `unsupported = true`).

## Method (the Rosetta stone, three independent keys)

1. **Musical known-plaintext**: the sample is named `fifth`; its opening pitch
   bytes are `43 37 2b` = 67,55,43 = G4,G3,G2 — Beethoven's 5th, Allegro con
   brio, as three 1-tick-staggered octave-stack chords, followed by the Eb stack
   (`33 27 3f` = 51,39,63), F stack (53,41,65), D stack (62,50,38), each ending
   in a 255-tick (0xFF delta) fermata. That confirms `pitch` = raw MIDI note
   number without any offset or cipher.
2. **Text-protocol Rosetta (F-37 + F-40)**: DEVO3.IG's 144 text events
   `n>inst,slot,vol,pitch,0,1` are Devo's "Whip It" riff (62=D4, 69=A4, 71=B4,
   67=G4, 72=C5 over 38=D2 bass) — the text layer already uses the SAME raw-MIDI
   pitch space and small-int tick deltas (`q>` 7..69). Text and binary are two
   encodings of one event semantics; text n> has explicit inst/slot/vol where
   the binary has the status nibble + f1/f3 flags + constant dur=0x57.
3. **Structural walk**: status bytes 0x90-0x94 at strict 6-byte intervals across
   13,408 stream bytes; declared chunk lengths (9998, 3410) match content byte
   counts exactly, including across the mid-stream `N>1,3410,` header.

## Evidence (fifth.igm)

- Container: `G#N>1,9998,` at file offset 2; `N>1,3410,` at offset 10009; both
  declared lengths = exact bytes present. 13,408 event-stream bytes total.
- 2,221 events parsed: 1,069 attacks (dur=0x57), 1,073 releases (dur=0x00),
  70 pitch-0 markers (statuses 0x92-0x94 only), 1 compressed 4-byte event at the
  chunk boundary (offset 9996: `90 00` + header + `57 01` = G4 re-articulation),
  7 control segments (0xC0-0xD0), end marker `fe 00`. 2 skipped bytes.
- Timeline coherence: staggered chord attacks (+1 tick per voice), short notes
  20-21 ticks, 255-tick fermatas, octave-alternating bass G2/G3 in the
  development section, final Eb-major triad held 99 ticks. 1,066 completed
  attack/release pairs; 77 releases unmatched (open item).
- Attack/release discriminator is `dur` (0x57 vs 0x00), NOT separate 0x8N/0x9N
  statuses — 0x8N never occurs.

## Grammar table

| Bytes | Field | Values | Meaning |
|---|---|---|---|
| 1 | status | 0x90-0x94 | note event, channel = low nibble |
| 1 | f1 | 0/1 | unresolved flag (1 on 57/1069 attacks; often 1 on a chord's middle release) |
| 1 | pitch | 36-87, 0 | raw MIDI note number; 0 = silence/advance marker |
| 1 | f3 | 0/1 | unresolved flag |
| 1 | dur | 0x57 / 0x00 | attack vs release (may be velocity or PSG envelope period, not ticks) |
| 1 | delta | 0-255 | ticks to next event (post-attached) |
| 4/10 | control | 0xC0-0xD0 | `[cN,0,0,x]` and 10-byte forms; c0..d0 table at EOF; semantics open (program-change analogy is a hypothesis) |
| 2 | end | `FE 00` | end of song |

## Honest negatives / open questions

- f1/f3 flag semantics unresolved. 0x92-0x94 pitch-0 markers unresolved.
- 0xC0-0xD0 control-event payloads (4- and 10-byte forms) not interpreted;
  the `ff 00` pair just before the c0 table is unexplained.
- 77 releases lack a matching attack (compressed-event pitch inheritance and/or
  pre-boundary voices); 0x91 never observed; `N>` arg1 always `1`.
- Delta unit unknown (no tempo marker); MIDI export uses raw ticks at 96 PPQN.
- Only ONE .igm sample exists in the corpus (F-37 census; discmaster lists ~46
  IGS files total) — grammar needs confirmation on more files. No text-`n>` /
  binary pair exists for the same song, so the text/binary mapping is semantic,
  not byte-for-byte.
- An ASCII-decimal long-delta form ("> 255 ticks") was hypothesized and NOT
  confirmed; max observed delta is 255.

## Decoder

`results/format-re/igs-music/igm_decode.py` (stdlib Python): parses `N>` chunks,
walks the event stream (6-byte, 4-byte compressed, control scan, end marker),
reconstructs the tick timeline, matches attack/release pairs, exports
`--events` / `--json` / `--mid` (format-0 MIDI, raw ticks). On fifth.igm:
1,066-note MIDI, first 12 attacks = G G G | Eb (Beethoven's 5th opening).
Validation data: `results/format-re/igs-music/igm-grammar.json`.

## Next steps

- Obtain more .igm files (discmaster ~46 IGS files) to confirm the grammar and
  crack f1/f3, the 0xC0-0xD0 table, and the delta unit.
- Diff a .igm against a known MIDI rendering of Beethoven's 5th to pin the tick
  rate (fermata = 255 ticks suggests a fine grid; eighth-note chords stagger 1 tick).
