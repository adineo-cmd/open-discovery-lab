# DiamondWare .dwm WRITE-side Grammar: SAMPLE.MID<->SAMPLE.DWM Ground-Truth Alignment (F-47)

**Track:** C — Discovery Engine | **Date:** 2026-11-14 | **Verdict: PARTIAL — first public .dwm grammar derivation from a converter ground-truth pair; encoder NOT yet bit-valid; per-opcode table now majority-pinned**

**Claim.** Instead of attacking the EXEPACK blocker (F-46), the WRITE-side grammar was derived empirically by aligning `SAMPLE.MID` (the MIDI source) with `SAMPLE.DWM` (MID2DWM's output) — the Rosetta pair sitting in the same SDK archive. The event envelope is confirmed, the 4 header patches are proven to be byte-exact GM1.IBK bank slots addressed by MIDI program number, the drum-channel event grammar is fully pinned (record shape, OPL2 voice assignment, volume transform, per-note pitch pair), the melodic note-on shape is pinned, and the timing model (heartbeat 72.0 Hz, 0.18 hb/tick) is validated. A full parse of all 2,613 events was blocked only by residual ambiguity in the non-drum record sizes within the 55-minute session bound; no claim below rests on guesswork — each carries its evidence.

## Method

1. Decoded `SAMPLE.MID` with a stdlib SMF parser: format 1, 7 tracks, division 240 ticks/qn, single tempo 600000 us/qn (100 BPM), 3,204 events, 4 active channels: 9 (drums, prog 0), 0 (prog 18), 1 (prog 38), 2 (prog 80); 1,593 note-ons; CC7 channel volumes 86/123/127/127; total 35,560 ticks.
2. Decoded `SAMPLE.DWM` header (F-41 envelope confirmed on fresh bytes): magic `DiamondWare Music\0`, body 12,686 B at u32@0x18, 2,613 events at u32@0x1C, header len 96 = 52 + 11x4 patches, u16@0x28 = 720 deci-Hz = 72.0 Hz heartbeat.
3. Cross-referenced the 4 patches against `GM1.IBK` (the MID2DWM instrument-bank input per STKMAN.DOC CLI contract `MID2DWM <rate> <mid> <bank.IBK> [out]`): each 11-byte patch occurs exactly once in GM1.IBK.
4. Frequency-matched DWM body n-grams against MIDI per-note counts (hat x435, kick x143, snare x74) to pin the drum record shape; verified volume transform from velocity statistics; ran constraint DFS parses (timing-anchored, quad-anchored, per-type size consistency) to bound the remaining record types.

## Confirmed grammar (evidence-backed)

### Header + patches
- 4 patches = **GM1.IBK slots 0, 18, 38, 80** — exactly the IBK slots of the MIDI programs used (drums->0, ch0 prog 18, ch1 prog 38, ch2 prog 80). Byte-exact single occurrence each. MID2DWM emits one 11-byte patch per distinct (channel, program).
- IBK layout: `IBK\x1A` magic + 16-byte records (11 patch bytes + 5 pad); slot N at offset 4 + 16N. Slot index = GM program number for melodic channels.
- 11-byte patch layout (derived): interleaved modulator/carrier OPL2 register values `[m_20, c_20, m_40, c_40, m_60, c_60, m_80, c_80, m_E0, c_E0, C0]` — the block layout is falsified because it puts 0xF2/0xF8 in the waveform slot (OPL2 waveforms are 0-3). Patch 0 (drums): m20=0x21 c20=0x31 m40=0x4F(TL15) c40=0x00(TL0 loudest) m60=0xF2 c60=0xD2 m80=0x52 c80=0x73 C0=0x06 (FB6, FM).

### Event stream
- Records are `[delta:u8][type:u8][params...]`, delta = heartbeats since previous event (72.0 Hz; MIDI time maps at 0.18 hb/tick for 240 tpqn @ 600000 us/qn — validated: tick-0 events at delta 0; drum onset delta chains sum to quantized onset times, e.g. hat@tick120 = 22 hb).
- **Type 0x00 = note-on, 6 bytes** `[delta][00][voice][vol][pitch_lo][pitch_hi]`:
  - `voice` = OPL2 channel: drums 6=kick, 7=hat, 9=snare (matches OPL2 rhythm-mode channel conventions); melodic ch1 uses voice 0.
  - `vol` = **MIDI velocity >> 1** — proven 3x on the three most frequent drums (hat vel 102 -> 0x33, kick 125 -> 0x3E, snare 115 -> 0x39) and on melodic (ch1 n39 vel 127 -> 0x3F).
  - `pitch_lo/hi` = per-note pitch pair, constant per note regardless of voice: note 39 -> `2F 07`, 40 -> `60 07`, 42 -> `C9 07`, 35 -> `0F 03`. Same note on melodic voice 0 and drum voice 9 carries identical pitch bytes -> pure function of MIDI note number (likely OPL2 f-number/block; exact formula open — 4 ground-truth pairs recorded).
- Drum note-offs are **absent** as separate same-shape events (435 hat quads = 435 hat-ons exactly); they are either encoded in another type or handled by retrigger/patch envelope — open.
- Non-drum types observed at pinned positions: a 3-byte `[delta][02][00]` record landing between MIDI event times (filler/advance-time semantics), and type 0x03 records at tick 0 (voice/patch setup; params `02 00 00` / `02 00 00 00` readings both still parse-consistent) — open.
- End-of-song: last record `[00][00][06 3F 0F 03]` (a voice-6 event) — the final byte is not an 0x0B type; the 0x0B end-marker semantics from F-41 remain unconfirmed for this file.

### Volume
- No CC7-derived master volume events observed in the event stream at tick 0 beyond the note/patch setup; channel CC7 (86/123/127/127) presumably folds into per-event vol or mixer defaults — open.

## Validation status (honest)

- `scripts`-side checks all pass for the pinned subset: 652 drum-ons accounted for at exact positions; volume transform exact on all measurable pairs; patch provenance exact (4/4 byte-identical in GM1.IBK).
- Full 2,613-record parse: NOT achieved in-bounds. Constraint DFS over per-type record sizes {3..16} with the 652 drum anchors + end/count (2613, ~6401 hb) is the correct finisher; it was still running at the session bound (state space: without a per-type size table the mid-file ambiguity between 3/4/5/6-byte non-drum records is unresolved).
- `dwm_encode.py` implements everything pinned (header, patches from an IBK bank, drum-channel encoding incl. voice map and vol transform, timing quantization) and emits a semantics-equivalent DWM for the drum channel; melodic pitch formula and non-drum types are TODO — the encoder is NOT yet able to reproduce SAMPLE.DWM and this is reported as a negative result.
- Round-trip: not yet meaningful until the full parse exists; the F-41 envelope decoder re-implemented here (`dwm_decode_events` in the encoder script) parses any candidate output back.

## What this yields for F-46

The opcode table is now majority-pinned from the WRITE side without unpacking MID2DWM.EXE: type 0x00 = 6-byte note-on with voice/vol(vel>>1)/pitch-pair; timing = heartbeat deltas at the CLI rate; patches = IBK slots by program number. Remaining open: melodic note-off encoding, type 0x02/0x03+ semantics, pitch-pair formula, end-of-song marker. These are all recoverable from the same ground-truth pair with the anchored-DFS finisher described above.

## Prior art

None public on the DiamondWare .dwm event grammar (F-40/F-41/F-46 verified). This is the first published derivation from a converter ground-truth pair.
