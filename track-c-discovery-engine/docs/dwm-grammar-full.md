# DiamondWare .dwm Grammar: Complete Event Table via Anchored-DFS Finisher (F-53)

**Track:** C — Discovery Engine | **Date:** 2026-11-14 | **Verdict: FULL — the .dwm event grammar is now fully derived from the SAMPLE.MID<->SAMPLE.DWM ground-truth pair; every one of the 2,613 events parses under a 3-type table, and every event maps to a MIDI event or a documented converter action. Byte-exact re-encode is the one open item.**

**Claim.** F-50 pinned the envelope and the drum subset but left five unknowns: per-type sizes for non-drum records, melodic note-off encoding, the pitch-pair formula, type-0x03 semantics, and the end-of-song marker. All five are now closed. The finisher is exactly the anchored partitioning F-50 proposed: the 652 velocity-stable drum quads split the 12,686-byte body into 653 short segments (233 empty, max 73 B); a chain DP over per-segment (delta-sum, event-count) options — with each anchor required to land on an unused onset time of its note — collapses the joint parse to a single time-chain, and a CSP over 3,788 surviving segment parses forces the complete size table. One wrong assumption from F-50 fell out on the way: the "end ≈6401.8 hb" estimate. The file actually ends at heartbeat 6394, the last MIDI drum onset; the MIDI end-of-track meta is not encoded at all.

## Complete grammar

Records are `[delta:u8][type:u8][params...]`, delta = heartbeats since the previous record (72.0 Hz; 0.18 hb/tick at 240 tpqn, 600000 us/qn). The stream is strictly time-ordered and the song ends when the records run out — there is **no end-of-song marker record**.

| type | size | shape | semantics |
|---|---|---|---|
| 0x00 | 6 | `[d][00][voice][vol][pl][ph]` | note-on. `vol` = MIDI velocity >> 1. `voice` 0-5 = melodic (dynamically allocated), 6 = kick, 7 = hi-hat, 9 = snare. `(pl,ph)` = pitch pair, pure function of MIDI note |
| 0x02 | 3 | `[d][02][voice]` | note-off on melodic voice 0-5. Drums emit no note-offs (envelope decay) |
| 0x03 | 4 | `[d][03][patch][voice]` | patch assignment: load header patch `patch` (0=drums, 1/2/3 = IBK slots 18/38/80) onto melodic voice `voice` |

F-50's "3-byte filler `[d][02][00]`" was a misreading — it is a genuine note-off on voice 0. Type 0x03 is emitted only when a voice must switch instrument (122 assignments for 916 note-ons); a voice keeps its patch until a note needing a different patch reuses it.

### Pitch pair (the formula, modulo one constant)

`(pl, ph)` is a 12-bit OPL2 frequency word: **fnum = ((ph & 3) << 8) | pl, block = ph >> 2**, f = C·fnum/2^block. Evidence: the block-1 ladder fnum 769/815/864/915/969 maps to MIDI 38/39/40/41/42 with exact semitone ratios (1.0590-1.0601); the same fnum at block+2 is the note two octaves down (`c9 07` = 42 vs `c9 0f` = 18); the same pair appears on melodic and drum voices unchanged. The absolute constant C fits at 0.1912-0.1917 Hz depending on pair (pair-quantized rounding) — pinned to ~0.9% but not to a clean constant (49716/2^18 = 0.18959 is close but off); likely a rounded per-note table in MID2DWM. Honest open item.

## How it was derived (anchored-DFS finisher)

1. **Anchor partition.** The three dominant-velocity drum quads (`07 33 c9 07` hat, `06 3e 0f 03` kick, `09 39 60 07` snare) occur exactly 652 times = record starts `[d][00][...]`. They partition the body into 653 segments.
2. **Per-segment option enumeration.** Within a segment (max 73 B), a bitmask DP enumerates all feasible (Σdelta, count) parse options; deltas are file bytes, so the sum is parse-dependent.
3. **Chain DP.** Walk the anchors in body order carrying (cum time, per-note next-unused-onset pointer, count bitmask). Each anchor must land exactly on an unused quantized onset of its note (this also handles the 7 drum hits that have no quad anchor — see below). Result: exactly **1 state survives** all 652 anchors; total non-anchor count 1961 is forced (2,613 − 652).
4. **CSP for the size table.** Forward/backward viability prunes segment options (558 of 653 segments then have a unique option); 3,788 parses survive. Single-parse segments force 0x00=6 and 0x02=3 outright; the CSP over the rest converges to `0x00:6, 0x02:3, 0x03:4` (a 10-byte 0x03 alternative also parse-feasible is rejected by semantics — its "params" carry no patch/voice structure).
5. **Full parse.** 2,613 records, end cum 6394 = 6372 (last anchored hat) + 22 (`0x16` delta of the first tail record).

## Validation (all checks pass)

- **Counts:** 1,575 × 0x00 + 916 × 0x02 + 122 × 0x03 = 2,613 = header event count (exact).
- **Note-ons/off symmetry:** per-voice melodic note-ons = note-offs exactly (220/183/143/125/128/117 for voices 0-5).
- **Drums complete:** 659/659 MIDI drum onsets are in the file — 652 carry the dominant-velocity quads; the other 7 have different velocity bytes and were invisible to F-50's fixed quads. The file's last three records (hb 6394) are exactly the three simultaneous final hits: `09 3f 2f 07` (ch9 note 39, vel 127), `09 1b 60 07` (snare vel 54), `06 3f 0f 03` (kick vel 127).
- **Volume:** every melodic `vol` = velocity >> 1 on uniquely-matched records (F-50's transform, now file-wide).
- **Patch semantics:** 0x03 params are only `01 vv`/`02 vv`/`03 vv` with vv in 0-5 — precisely the 3 melodic patches × 6 melodic voices; patch 0 (drums) is never assigned mid-stream.
- **Timing:** every record's cumulative heartbeat lands on a quantized MIDI event time or inside a drum-gap window; anchor times are exact unused onsets of their note.

## Honest negatives

1. **Byte-exact re-encode not completed in bounds.** All encoding primitives are known (this table + header/patches from F-50), but a bit-exact rebuild additionally needs MID2DWM's voice-allocation order (which free voice a note-on takes), same-heartbeat event ordering (offs vs ons vs patch changes), and the drop policy for the 25 melodic notes lost to voice exhaustion (941 MIDI melodic note-ons vs 916 encoded). These are recoverable from the same ground truth by replaying the parse against the allocator.
2. **Pitch constant C** pinned only to ~0.9% (pair-quantized).
3. The 7 non-quad drum records were found via the tail, not via an exhaustive velocity sweep — a general converter would emit any vel byte; the grammar covers this trivially (`vol = vel>>1`), but only 5 distinct drum velocities are ground-truthed.

## Artifacts

- `results/format-re/diamondware-census/dwm-grammar-full.json` — machine-readable grammar + counts.
- Session scripts (workspace `scripts/`): `finisher2.py` (global bitmask DP), `chain.py` (anchored chain DP), `phaseC.py`/`phaseD.py` (option viability), `phaseE.py` (final pipeline: chain DP + count-aware backward pass + CSP + parse dump `/tmp/parse_v4.json`).

## Prior art

None public on the DiamondWare .dwm event grammar (F-40/F-41/F-46 verified). This completes the first full derivation from a converter ground-truth pair; combined with F-50 (header, patches = IBK slots by program, timing) the format is now writable end to end modulo allocator tie-breaks.
