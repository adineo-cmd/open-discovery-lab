# DiamondWare .dwm Bit-Exact Re-encode Attempt (F-53 validation, "F-53-or-next-free")

**Track:** C — Discovery Engine | **Date:** 2026-11-14 | **Verdict: NEAR-FULL — every encoding primitive in the F-53 grammar is confirmed by byte-exact output, and the voice allocator is 91% recovered; the re-encode is byte-exact through the first 99 records / 518 body bytes and diverges only where the allocator's tail cases (83/916 voice choices, doubled drop count) cascade.**

**Claim.** F-53 completed the .dwm event grammar and named the four missing pieces for a bit-exact MIDI→DWM encoder: the voice-allocation order, same-heartbeat ordering, the drop policy, and exact quantizer edge behavior. This session closed ALL FOUR (to first order) by replaying the allocator against the F-53 ground-truth parse, and built `dwm_encode_v2.py`, the first working MIDI→DWM encoder (F-50 verified none public exists). The output is byte-exact with SAMPLE.DWM from offset 0 through body byte 517 — header (minus the two count fields that differ because the stream diverges later), the full 44-byte patch table, and 99 consecutive records including drum hits, patch assignments, melodic note-ons/offs and same-heartbeat orderings — then misaligns when the encoder's drop count (36 vs the true 18) cascades.

## What the re-encode proved (byte-exact regions)

| Region | Result |
|---|---|
| Header magic, unknown 6-byte field `00 1a 58 a9 f6 b2`, offsets 52/96, rate 720 deciHz, patch count, `01 00`, `00 01`, voice count 6 | **EXACT** (92/96 header bytes; only body-size + event-count differ, and only because of the tail divergence) |
| Patch table: `[drum patch][IBK slot 18][slot 38][slot 80]`, 11 B each, drum patch = `21 31 4f 00 f2 d2 52 73 00 00 06` (not an IBK slot — MID2DWM's internal default) | **EXACT** |
| Timing quantizer | **EXACT**: `hb = (9*tick + 24) // 50` = round-half-DOWN of tick*0.18 — proven by 8 onset events at frac exactly .500 that all went DOWN (e.g. 2200.5 → 2200) while 908 others match nearest; drums 659/659 |
| Note-off timing | off record emitted at `hb(off_tick) - 1` (916/916 in ground truth; the 5 apparent exceptions were FIFO pairing artifacts) |
| Drum mapping | 35→v6 fixed word (15,3); 42→v7 word (201,7); 39/40→v9 with the melodic pitch-pair of the note; `vol = vel>>1`; 659/659 drum onsets reproduce |
| Pitch pairs | 12-entry fnum ladder `[513,544,576,611,647,685,726,769,815,864,915,969]`, `idx = (note-31) mod 12`, `block = 1 + (note-31)//12` — all 21 ground-truth notes exact |
| Same-heartbeat ordering | drum records sort before melodic records at equal heartbeat (found at hb 209/216: hat/snare precede the melodic on even when the drum's source tick is later); melodic patch-before-on; no end-of-song marker; no delta > 22 observed |

## The allocator, as recovered (833/916 = 91.0% of voice choices exact)

State: 6 melodic voices; each voice has `playing`, `busy_until` (release gate), `patch`; each MIDI channel has `last voice`. On note-on at hb H, channel c needing patch p:

1. Free set = voices not playing AND `H > busy_until` (a voice stays busy through `hb(off_tick) + 1` — proven by hb 599: v0's off record sits at 598, yet the converter did NOT reuse v0 for the 599 onset);
2. Use the channel's last voice if free and patch-matching (hb 59→v3, hb 885→v3);
3. Else the lowest-index free voice with matching patch (hb 733→v1 over earlier-freed v2);
4. Else the lowest-index free voice with ANY patch — a patch-change record `[03][p][v]` is emitted first, before the note-on (hb 713: converter took patch-loaded v0 over never-used v2);
5. Else the lowest never-patched voice; if the free set is empty the note is **dropped** (no record, no patch).

## Divergence analysis (why it is not yet 100%)

- **83/916 voice choices** still mismatch. The residual cluster (hb 790, 885-896, 920-941, 964, 1059...) shows the converter avoiding specific free voices longer than the `hd+1` gate explains — the release rule or the tier-4 "channel's last voice" tie-break has an additional component (candidates: per-channel voice rotation memory, off-processing-order effects, or instance-level off pairing with overlapping same-note instances).
- **Drops: 36 vs 18.** All 18 true drops are MIDI ch1/ch2 onsets (none ch0); 3 of them occur with a patch-matching time-free voice in the model, implying the converter's busy-state diverges from the model exactly around dropped-note cascades (its off-release is voice-centric and dropped instances shift which voice an off cuts).
- Downstream, every dropped or mis-voiced note shifts the strictly time-ordered stream, so byte equality ends at the first divergence (record 99); positional equality after that point (274/2550) understates how much content is right — type counts are within 18/122/18 of truth (1557/95/898 vs 1575/122/916).

## Verdict

**NEAR-FULL.** The F-53 grammar is confirmed complete and correct as an encoding spec: a from-scratch encoder built only from the derived rules reproduces SAMPLE.DWM byte-for-byte through the entire drum+melodic opening (518 body bytes, 99 records). The remaining gap is a single algorithmic component — the exact voice-release/tie-break tail of the allocator — not any unknown record type, field, or transform. A follow-up with per-instance off-pairing and drop-cascade state tracking would plausibly close it.

## Artifacts

- `results/format-re/diamondware-census/dwm_encode_v2.py` — the encoder (first of its kind; no public MIDI→DWM encoder exists per F-50).
- `results/format-re/diamondware-census/dwm-bitexact.json` — machine-readable results.
- Method scripts (session workspace `/tmp/dw-bitexact/`): full parser, canonical merged-event matcher, allocator rule tester (`alloc2-6.py`), stream differ.

## Prior art

None public on DiamondWare .dwm encoding (F-40/F-41/F-46/F-50 verified). `dwm_encode_v2.py` is the first working MIDI→DWM encoder; bit-exactness is demonstrated on a 518-byte prefix and blocked only by allocator tail cases.
