# DiamondWare EXEPACK Decode Validated Against the Ground-Truth Pair — Flag-Trajectory Coupling Disproven at Machine Level (F-58)

**Track:** C — Discovery Engine | **Date:** 2026-11-14 | **Verdict: NEGATIVE-with-PROOF** (the named F-57 next step — "re-simulate with flag trajectory coupled to the write-relative stream window" — was executed with an instruction-exact rebuild of the stub and produces a decisive negative: there is **no flag-trajectory freedom at the machine level**; the flag words are read from a fixed, pristine base (DS = image_base+0x7E1 paras) and the END at token 2759 is unavoidable under the disassembled machine. The decoded output does **not** match the SAMPLE.DWM body — it is the unpacked MID2DWM.EXE program image head (real x86 code), so the .dwm body is not EXEPACK-compressed and F-53's grammar stands unchallenged. New hard result: the false END is **systematic across all four SDK binaries** — the pristine-stream decode reconstructs none of the four images, each falling short of its stub-header-mandated entry point. The F-53 grammar was independently re-validated exact against the local SAMPLE.DWM (2,613 events, all counts, end hb 6394, single parse).)

**Claim.** This session rebuilt the F-56/F-57 exact-machine simulation from a fresh capstone + objdump disassembly of the full 347-byte stub (extracted to `/tmp/f47b/stub.bin` from MID2DWM.EXE load-module offset 0xBDA0), reproduced every F-56/F-57 number, then executed the F-57 named next step and the known-plaintext validation.

## What reproduced

- END at token 2759, output 17,814 B, consumed 4,081 B (SI=0xFF1), exactly one NORM (token 1181, ES −0x5F paras, physical write preserved at 0x1A1C; final DI = 0x4B86 = the F-56 19,334 figure confirmed as DI-inflated).
- Tokens 1–8 decode to literals `A1 44 00 0B 06 42 00 74` = plausible Borland code (`mov ax,[0x0044]`; …), confirming the stream starts at payload[0] with LSB-first 16-bit flag words.
- F-57's overtake prediction 0xA379: a force-continue sim measured the writer/flag-reader overtake at **out = 41,848** (token 6421, si 9,576) — within 7 bytes of the predicted 41,855.

## Instruction-exact corrections and confirmations (new)

1. **Init bases verified instruction-by-instruction**: after the backward chunked move (one chunk, 0xBDA paras, `rep movsw` with DF=1, covering exactly `[image_base, image_base+0xBDA0)` → `[image_base+0x7E10, image_base+0x13BB0)`), the code sets `ES=DX=image_base` (writer) and `DS=BX=image_base+0x7E1 paras` (flag base = moved copy). Entry: `push cs/pop ds` → stub self-copy to CS0+0x7E1 → `lret` into the moved stub → move → decode.
2. **The real entry, exactly**: DONE phase (`0xFC`) pops ES_orig (=PSP), BX=PSP+0x10=image_base; the reloc walker consumes stub data `00 01 00` (zero fixups); then `DI=[stub+4]` (w2=0x80, real SP), `SI=[stub+6]` (w3=0x1444, real SS paragraph offset), `w1 += image_base` at 0x142, and `ljmp cs:[bx]` (bx=0) reads the far pointer **at moved_stub:0 = header words w0:w1** = `0x0010:0x135F` → **entry = image offset 0x135F0+0x0010 = 0x13600** — F-57's entry figure confirmed exactly; real SS:SP = image_base+0x1444 paras : 0x0080.
3. **The dictionary read is `mov al,es:[bx+di]` — the writer's own segment.** Pre-NORM non-wrapping reads are write-relative forward reads: physical source = write_off + 0x10000 − dist, i.e. **stream offset = write_off + 0x81F0 − dist** (exact constant), confirming F-57's write-relative stream window with the exact machine constant — the "reverse overtake" formula `write+dist` of F-57's V3 variant is a heuristic, not the machine's form. Post-NORM all reads are backward (write − dist) because DI ≥ 0x2000 and BX ≥ 0xE000 force the wrap; F-57's three-region map is confirmed.
4. **The flag side has zero freedom**: flags, literals and operands are all `lods` from DS:SI; DS changes only at NORM (`DS += oldSI>>4`, physical-preserving). The writer (17,814 max) never reaches the flag window (0x7E10+si, ≥ 0x7E10) before SI hits 0xFF1, so the flag words are pristine payload[si] throughout. **The END at token 2759 — count byte payload[0xFF0] = 0x00, verified raw (payload[0xFEF] = 0x80) — is unavoidable under the disassembled machine.** F-57's "flag-word base/trajectory coupling" is disproven as a code-level mechanism: there is no register or memory path by which the flag trajectory can couple to the write window.

## Known-plaintext validation: honest negative

The decoded 17,814 B were compared byte-for-byte against the SAMPLE.DWM body (12,686 B): **165/12,686 matches (noise), first mismatch at offset 0**. The decoded output is the unpacked program image head (`A1 44 00 0B …`), not the event stream. The task's premise that the EXEPACK decode produces the .dwm body is false; the .dwm body is stored raw and F-53's grammar is the complete description of it. Conversely the F-53 grammar was **re-validated exactly** against the local ground truth this session: single parse consumes 12,686/12,686 B → 2,613 events, types 0x00=1,575 / 0x02=916 / 0x03=122, 916 melodic note-ons = 916 note-offs, 659 drum note-ons, end heartbeat 6,394, first event `[0,0,7,51,201,7]` = F-53's `07 33 c9 07` quad, last three events the special-velocity drum hits at hb 6394. Every count matches F-53.

## The false END is systematic — new hard result

The four SDK binaries share a **byte-identical 347-byte stub** (diff = header words only, verified across FINDSB/PLAYDWD/VOC2DWD/MID2DWM). Running the same instruction-exact sim on each:

| binary | payload B | END out | entry needed (w1*16+w0) | short by | notes |
|---|---|---|---|---|---|
| FINDSB.EXE | 19,792 | 14,532 | 28,626 (0x6FD2) | 14,094 | writer wrote 3,556 B into the moved stream before END; writer only 256 B behind flag pointer |
| PLAYDWD.EXE | 21,312 | 10,998 | 30,466 (0x7702) | 19,468 | |
| VOC2DWD.EXE | 22,144 | 7,390 | 38,034 (0x9492) | 30,644 | |
| MID2DWM.EXE | 48,544 | 17,814 | 79,360 (0x13600) | 61,546 | |

None of the four images can be reconstructed from the pristine stream under the disassembled machine — the END the machine hits is false in every case, yet the machine provably reaches it. **This is the central open contradiction.** Force-continuing past the END (skipping the 0x00) fills the geometry (overtake at 41,848 as computed) but the token stream immediately desynchronizes: post-overtake output degenerates into self-copy loops (`<<<<<<<<<<` runs), and the entry region 0x13600 lands on packed payload bytes (payload[0xB7F0]) that disassemble as garbage — impossible for a shipping program.

Two new structural facts constrain the resolution: (i) the payload tail `[0xB7F0, 0xBDA0)` is **verbatim** Borland runtime data (`<<NMSG>>` marker, ctype-style tables) — the payload is not a homogeneous compressed stream; (ii) the region `[0xFF1, 0xB7F0)` is stream-continuation-like (compressed-looking) but is not consumable under the pristine-flag model. The missing piece is the packer's compressed/verbatim block-boundary semantics — how the encoder lays out stream blocks and verbatim tail so that the decoder's single DS:SI stream skips the 0x00. FINDSB is the tightest probe (writer 256 B behind the flag pointer at END; smallest stream).

## What this yields

- The .dwm opcode table as a *stream grammar* is complete and now double-validated (F-53 + this session's independent re-parse): 0x00 = 6B note-on `[delta][00][voice][vol][pitch_lo][pitch_hi]`, 0x02 = 3B note-off `[delta][02][voice]`, 0x03 = 4B patch assignment `[delta][03][patch][voice]`, no end marker. Full per-event list published in dwm-grammar-full-v2.json.
- The EXEPACK decode path to the converter's code (and any further opcode semantics beyond the stream grammar) remains blocked by the systematic false-END contradiction, now sharply characterized: machine-exact, all four binaries, with the verbatim-tail fact pointing at block-boundary semantics as the next attack surface.

## Prior art

F-56 (token grammar, DI-inflation correction), F-57 (overtake design, write-relative forward window — forward window confirmed here with the exact constant 0x81F0; flag-coupling hypothesis disproven here). No public prior art on TLINK EXEPACK block-boundary semantics found.

Artifacts: `/tmp/f47b/` (sim1.py exact-machine sim + DWM comparison; sim2.py four-binary systematic run; sim3.py force-continue with overtake tracking; stub.bin; events.json; dwm-grammar-full-v2.json; dec_v3.bin 17,814 B; dec_cont.bin 131,275 B).
