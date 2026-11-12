# DiamondWare .dwm Event Grammar Decode (F-41)

**Track:** C — Discovery Engine | **Date:** 2026-11-13 | **Verdict: PARTIAL** (container FULL; event envelope RESOLVED; per-opcode semantics PARTIAL)

**Claim.** The DiamondWare Sound ToolKit `.dwm` music format is now described from vendor primary sources (STK 1.02 SDK C headers + player source + manual) and validated arithmetically against 8 files (7 game samples from F-40 + the SDK's own SAMPLE.DWM). The 72.8 Hz heartbeat hypothesis from F-40 is **CONFIRMED by the vendor's own C source**. F-40's "constant signature" is **resolved as instrument-patch data, not a signature**. The event-stream envelope (4/5-byte records, `[delta][type][params]`, `0x0B`=end-of-song) is **proven unique** by an exhaustive length-pair algebra across all 8 files. Per-opcode semantics remain partial (honest negative).

## Method (C-source-first, disassembly corroboration)

1. **Vendor SDK mined** (re-verified on disk at `/tmp/dw-sdk`, from archive.org `DiamondWaresSoundToolKit_1020`, stk12.zip):
   - `PLAYDWM.C` v1.02 (player source): calls `dwt_Init(dwt_72_8HZ)`; comments document 72.8 vs 145.6 Hz trade-off.
   - `DWT.H`: `#define dwt_72_8HZ 2 /* 72.8 Hz */`; supported timer rates {18.2, 36.4, 72.8, 145.6} Hz.
   - `DWS.H`: `dws_MPlay` validation errors `NOTADWM=16`, `NOTSUPPORTEDVER=17`, `INTERNALERROR=18`.
   - `STKMAN.DOC`: `MID2DWM <rate> <midifile>[.MID] <instrfile>[.IBK] [outfile[.DWM]]` — rate is an arbitrary parameter (custom timers allowed); MIDI type-1 input; >64K songs supported.
2. **Header arithmetic** verified with `assert` on all 8 files (below).
3. **Event grammar** cracked by exhaustive grid search over record-length pairs (short, long) ∈ [1..8]² requiring `body_len = a·short + b·long`, `a+b = event_count` (u32@0x1C) to hold **simultaneously for all 8 files** — exactly one solution: **{4, 5}**. Confirmed by the end-of-song marker `0x0B` landing on the type byte of the final record in validated parses.
4. **Disassembly** (capstone 5.0.7): `MID2DWM.EXE` = plain DOS MZ, but Borland EXEPACK-compressed (not unpacked — negative). Pivoted to `DWS.LIB` (OMF): parsed 21 modules; recovered API symbols (`DWS_MPLAY`, `DWS_UPDATE`, …) in `dws.ASM`; engine internals are symbol-obfuscated (`dwsIIII.ASM`-style 1/I/0/l mangling). Cross-module FIXUPP resolution left as future work.

## Resolved header (vendor-source-verified + arithmetic on 8/8 files)

| Off | Type | Meaning |
|----|------|---------|
| 0x00 | 18 B | `"DiamondWare Music\0"` magic (→ `dws_MPlay_NOTADWM` if bad) |
| 0x12 | u16 | `0x001A` constant (role unknown; likely version tag → `NOTSUPPORTEDVER`) |
| 0x14 | u32 | checksum-like, varies per file (unconfirmed) |
| 0x18 | u32 | **body length** (== filesize − header_len in 8/8) |
| 0x1C | u32 | **event count** (== exact DP record count in 8/8) |
| 0x20 | u32 | `52` constant, all files (role unknown) |
| 0x24 | u32 | **header length = 52 + 11·N** (F-40's `74 + 11·(byte@0x2A − 2)` ≡ same) |
| 0x28 | u16 | **heartbeat rate, deci-Hz**: 720→72.0 Hz, 728→72.8 Hz, 750→75.0 Hz observed |
| 0x2A | u16 | **N = number of embedded 11-byte OPL2 patches** (from the .IBK bank) |
| 0x2C | u16 | `1` (all files) |
| 0x2E | u16 | `0x0100` (all files) |
| 0x30 | u32 | `6` (all files; per-patch stride? unconfirmed) |
| 0x34 | N×11 B | **OPL2 instrument patches**. F-40's "constant signature `21 31 4F 00 F2 D2 52 73`" = patch #0's parameter bytes (all surveyed files share the same first instrument) — **not a signature** |
| 0x3F | u8 | flags: 01 / 11 / 31 observed |

**Timing: seconds = delta_ticks ÷ (u16@0x28 ÷ 10).** The F-40 hypothesis "u16@0x28 = heartbeat ×10" is **CONFIRMED**: vendor source fixes the heartbeat at 72.8 Hz (dwt_72_8HZ) and files store 728/720/750 deci-Hz, matching `MID2DWM <rate>`'s arbitrary-rate contract in the manual.

## Event grammar (envelope proven; per-opcode semantics partial)

```
record := delta:u8  type:u8  params[2]   # 4-byte record
        | delta:u8  type:u8  params[3]   # 5-byte record
delta      : heartbeat ticks until the next record (cumulative => event times)
type       : opcode; 0x0B = END-OF-SONG (verified as final record's type byte)
type 0x00-0x0F : dominant operational range (76-78% of records across files)
```

**Uniqueness proof:** only {4,5} satisfies the two-count algebra on all 8 files:

| File | body | events | split (4-byte, 5-byte) | rate | song len | END 0x0B |
|------|-----:|-------:|------------------------|-----:|---------:|:--------:|
| combat.dwm | 3461 | 698 | 29 + 669 | 75.0 Hz | 136 s | reachable |
| LAKE.DWM | 498 | 111 | 57 + 54 | 75.0 Hz | 49 s | **verified** |
| LBL5.DWM | 305 | 68 | 35 + 33 | 72.8 Hz | 33 s | reachable |
| MC07.DWM | 3145 | 705 | 380 + 325 | 72.8 Hz | 156 s | **verified** |
| SAMPLE.DWM | 12686 | 2613 | 379 + 2234 | 72.0 Hz | 862 s | reachable |
| SPAC1.DWM | 9788 | 2015 | 287 + 1728 | 72.8 Hz | 621 s | reachable |
| TOWN.DWM | 3759 | 836 | 421 + 415 | 72.0 Hz | 329 s | reachable |
| SDK SAMPLE.DWM | 12686 | 2613 | 379 + 2234 | 72.0 Hz | 862 s | reachable |

**F-40 motif resolution:** F-40's "6-byte note motif `[06|09][note][inst][vol][dur u16 LE]`" was a mis-framing of two adjacent 4/5-byte records: `06`/`09` are frequent **delta** values, not opcodes.

## Honest negatives

- `MID2DWM.EXE` is Borland EXEPACK-compressed; unpack+disassemble remains open (the writer would confirm opcode semantics directly).
- `DWS.LIB` event loop: OMF parsed, API names recovered, but engine modules are symbol-obfuscated and FIXUPP cross-module fixups were not resolved in-session.
- Without the vendor event loop, record boundaries in arbitrary files are DP-scored (byte- and count-exact everywhere, but boundary assignment is only probabilistic where the type range is unbounded).
- Per-opcode semantics (which types are note-on/off, instrument change, volume, duration) not yet pinned; params of 4- vs 5-byte records unmapped.

## Prior art

None public (F-40 verified 2026-11-13): this is the first public `.dwm` grammar description, vendor-source-corroborated. Decoder tool (`dwm_decode.py`, stdlib-only) kept in session scratch per repo rules; methodology reproduced in the JSON artifact.
