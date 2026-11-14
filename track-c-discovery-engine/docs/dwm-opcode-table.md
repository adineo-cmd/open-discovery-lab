# DiamondWare .dwm Opcode Table Attempt: MID2DWM.EXE EXEPACK Attack (F-46)

**Track:** C — Discovery Engine | **Date:** 2026-11-14 | **Verdict: PARTIAL** (EXEPACK stub FULLY reverse-engineered — first public documentation; unpacked-image recovery 42 bytes verified then blocked; per-opcode semantics still open)

**Claim.** The session goal was to unpack the EXEPACK-compressed `MID2DWM.EXE` (the .dwm *writer*) and pin the event opcode table. The packer is identified as the **Borland TLINK EXEPACK variant** (a distinct token format from the Microsoft EXEPACK 4.x documented on ModdingWiki). Its stub is here **fully reverse-engineered and published** — the decompression token grammar is now known except for one field (the long-run distance encoding). A Python unpacker decodes the stream and reproduces the first 42 bytes of the unpacked image as coherent Borland C0 startup code, then mis-decodes; enumerating all plausible long-run distance formulas (7 candidates × count variants × short-run variants, 56 combinations) produced **no** full decode, so the blocking unknown is pinpointed to exactly one encoding. The opcode table itself therefore remains unpinned; the envelope facts of F-41 stand unchanged.

## Method

1. **SDK re-acquired** (prior `/tmp` scratch was lost): archive.org item `DiamondWaresSoundToolKit_1020` → `stk12.zip` → `STK102.EXE` (LHa SFX v2.13S). The SFX uses a **non-standard LHA header layout** (documented below) that breaks `lhafile`; a pure-Python `-lh5-` decoder (ported from lhasa's `lh_new_decoder.c`) recovered **all 38 files at exact original sizes**, including `MID2DWM.EXE` (48,923 B), `PLAYDWM.C` (6,081 B), `SAMPLE.DWM` (12,782 B) — and, notably, **`SAMPLE.MID`** (13,261 B), the MIDI source of `SAMPLE.DWM` (a ready-made converter ground-truth pair for the next session).
2. **MZ header**: load module 48,891 B at file offset 0x20; entry CS:IP = `0x0BDA:0x000E` (near module end); `e_crlc=0`.
3. **Stub disassembly** (capstone 16-bit): entry code at CS:0x0E, decompressor loop from CS:0x21 onward; DONE/relocation code at file offset 48,876.
4. **Token walk** validated token-by-token against the stream; 56-variant brute force for the unresolved field.

## New finding 1: the SDK LHa SFX header variant (blocking artifact, now documented)

`STK102.EXE` (LHa SFX v2.13S) stores level-0-ish headers **without the standard skip/attribute bytes**, empirically:

```
[method "-lh5-" 5B][packed u32le][orig u32le][time u32le][res u16 = 0x0020][nlen u8][name][crc u16][ext u16]
data at method+24+nlen ... data ends exactly at the next header (chain-verified across all 38 entries)
```

`lhafile` (C ext) segfaults/misparses this; the pure-Python `-lh5-` decoder used is the lhasa algorithm (HISTORY_BITS=14, NUM_CODES=510, temp/code/offset trees per `lh_new_decoder.c`).

## New finding 2: Borland TLINK EXEPACK — complete stub anatomy

Stub header (7 words at CS:0, this file): `real_ip=0x0010, real_cs=0x135F, real_sp=0x0080, real_ss=0x1444, payload_paras=0x0BDA, shift_paras=0x07E1, stub_len=0x015B`. Packed relocation table at stub+0x158: bytes `00 01 00` = "word 0x0001" = **terminator with zero fixups** (consistent with `e_crlc=0`).

Runtime flow (all segment-arithmetic verified from the disassembly):

1. Entry `CS:0x0E`: `push es; push cs; pop ds`; copy the whole stub (0x15B bytes) up by `shift_paras` (0x7E1) paragraphs; `retf` into the copy.
2. Relocation-style move: the 0x0BDA-paragraph payload is copied up by 0x7E1 paragraphs, freeing [image_base, image_base+0x7E10) for the unpacked image (32,272 B initial hole; the image grows beyond it via pointer normalization — final CS 0x135F ⇒ image ≈ 79 KB, larger than the 48.5 KB payload: EXEPACK expansion via runs).
3. Decompressor (cld, forward): DS:SI = payload start, ES:DI = image start, both 0; bit-buffer = 16-bit **little-endian** words fetched by `lodsw`, bits consumed **LSB-first** (`shr bp,1`); literal/distance bytes and long-run words are **raw bytes interleaved in the same stream** (`lodsb`/`lodsw` share SI with the flag words).
4. Token grammar (verified: 36 consecutive tokens reproduce exact Borland C0 startup `A1 44 00 / 0B 06 42 00 / 74 0D / FF 36 ... 55 / E8 ...` — machine-code-coherent):
   - flag bit = 1 → **LITERAL**: next raw byte appended.
   - flag bit = 0 → **RUN**:
     - flag bit 2 = 0 → **SHORT**: 2 flag bits → `count = bits+2` (2..5); then 1 raw byte → `dist = 0x100 − byte` (1..256).
     - flag bit 2 = 1 → **LONG**: 1 raw word `w`; `hi=w>>8`; count-code = `hi&7`: nonzero → `count = code+2` (3..9); zero → 1 raw byte `c`: `0` = **END-OF-STREAM**, `1` = **pointer-normalize marker** (rewrites DI to `0x2000+(DI&0xF)` with ES adjusted −0x200, and DS/SI likewise — keeps the 8 KB negative-offset history window in-segment), `≥2` → `count = c+1` (3..256).
   - History read: `ES:[BX+DI]`, BX = `0xFF00|byte` (short ⇒ dist 1..256) or `((0xE0|(hi>>3))<<8)|lo` (long ⇒ dist 1..0x2000 under the natural reading).
5. DONE: walk the packed reloc table (`byte 0 → word: 0 = next section (+0xFFF paragraphs), 1 = end, else delta`), fix up segment words by image base, restore SS:SP from header, `ljmp cs:[0]` to `real_cs:real_ip`.

**The blocker.** The LONG-run distance as naturally read (`dist = 0x10000 − ((0xE0|(hi>>3))<<8 | lo)`) is rejected by the stream: the first LONG token (token 37, di=42) would demand dist=0x13EC. All 56 tested combinations of 7 distance formulas × 2 count formulas × 2 short-count bit orders × 4 short-distance formulas failed to fully decode. Since the SHORT form and the bit mechanism are verified, the residual unknown is confined to the LONG-run distance (or a yet-unnoticed stream-position subtlety at its word fetch). One candidate worth testing next session: the long form may encode a *copy-from-source-stream* or a 13-bit window with a different bias (e.g., `dist = ((hi&0x1F)<<8|lo) + bias`).

## What this yields for the opcode table (honest negative)

- The .dwm **envelope** remains as F-41: `{4,5}`-byte records `[delta:u8][type:u8][params]`, `0x0B` = end-of-song, heartbeat = u16@0x28 deci-Hz (72.8 Hz confirmed from vendor source `dwt_72_8HZ`; also used by the converter per `MID2DWM <rate>` CLI contract in STKMAN.DOC).
- `PLAYDWM.C` (read side) contains **no event dispatch** — it is a pure API caller (`dws_MPlay` etc.); the read-side switch lives in `DWS.LIB` (OMF, symbol-obfuscated). `DWS.H`, `DWT.H`, `STKMAN.DOC` contain **no opcode enumeration** (checked by keyword sweep).
- SAMPLE.DWM re-verified on fresh extraction: magic + all header fields identical to F-41 (body 12,686, events 2,613, hdrlen 96 = 52+11·4 patches, rate 720 deci-Hz, patch0 `21 31 4F 00 F2 D2 52 73 00 00 06`). Record split: 379 four-byte + 2,234 five-byte. Body contains 42 `0x0B` bytes; the final tail is `... 06 3F 0F 03` — the end marker is not the last type byte under a naive backward parse, consistent with F-41's "reachable" (not verified) status for this file.
- The 7 game samples from F-40/F-41 were not re-fetchable in this session's budget; all arithmetic claims above were re-verified on the SDK's own SAMPLE.DWM only.

**Next lever (singular):** resolve the LONG-run distance encoding (one field), finish the unpack, disassemble from CS:IP 0x135F:0x0010, and mine the write-side switch. The alternative path — align `SAMPLE.MID` ↔ `SAMPLE.DWM` (both now on disk) — can pin note-on/off/instrument/volume/tempo semantics empirically without the converter binary.

## Prior art

None public on the Borland EXEPACK variant's token format (Microsoft EXEPACK 4.x is documented at shikadi.net/moddingwiki; the two are different formats). The .dwm opcode table itself remains unpublished anywhere (F-40/F-41 verified).
