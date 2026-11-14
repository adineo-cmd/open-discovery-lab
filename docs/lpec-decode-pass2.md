# LPEC decode pass 2 — PCM synthesis path, bit pump, and CUnitter framing resolved

Date: 2026-11-14. Second pass on the Sony LPEC codec (continues F-48's LPEC.dll API map and F-47's bitstream census). Method: PyGhidra decompilation of the existing F-48 Ghidra project (Ghidra 12.2, x86:LE:32:default, LPEC.dll 402 functions) plus a fresh analysis of STVoice.dll (2219 functions) with an RTTI-driven CUnitter vtable walk. No Sony binaries or decompiled code committed — derived facts only.

## Claim

The LPEC decode chain is now resolved end to end at the structural level: the bit pump is an MSB-first bit accessor (`FUN_1000ef20`) over an input buffer refilled by virtual `vtable+0x14`; the synthesis core (`FUN_10005040`) reads a 2-bit frame type, a 1-bit block flag, and per-subframe (1-bit presence + 7-bit codebook-page-index) pairs, builds excitation from codebook pages selected by that index, and funnels through a double-precision overlap-add windowed by a per-mode LPC window (order 10 at 8 kHz, 16 at 16 kHz); `FUN_100059e0` is only the double-to-PCM16 saturating converter. The CUnitter* framing classes give the frame-length formulas **from code**: `CUnitterLpecLp` = 48/36/60 B per mode nibble, `CUnitterLpecSp` = 128/96/160 B — which **resolves the F-47 MSV 16k question: 128 bytes/frame** (mode 0x00/C0), confirmed on the real file (exactly 159.0 continuous 1024-bit frames, 96.2% type-0). LP mode resets frames at each packet boundary (21x48+6 tiling, integrality-forced); SP mode straddles packets (1014 not divisible by 128 — arithmetically forced).

## What decompiled vs what timed out

- Decompiled fully (fast, project reused from F-48, no re-analysis): pump ctor `FUN_10003a80`/`FUN_10003b10`, `SetFormat FUN_1000efe0`, pump `FUN_1000ee10` (vtable+0x14), pump step `FUN_1000f060`, bit accessor `FUN_1000ef20`, wrapper ctor `FUN_10004c50`, wrapper init `FUN_10004ec0`/`FUN_10005980`, synthesis converter `FUN_100059e0`, decode core `FUN_10005040` (2332 B), `SetParams FUN_10003e60` (1506 B), and 13 CUnitter methods in STVoice.dll. The earlier "decompiler timeout" pattern from the Hexagon case did not recur; the only friction was Ghidra not auto-creating functions at vtable-pointer targets (fixed with DisassembleCommand + CreateFunctionCmd).
- Not yet decompiled (next pass): `FUN_10004960` (excitation build), `FUN_1000f430` (post-filter), `FUN_1000f1c0` (windowed overlap-add), `FUN_10005ca0`/`FUN_10005bf0` (overlap stages), `FUN_10005d50`/`FUN_1000ab80` (buffer prep) — the synthesis interior below the core.

## Synthesis structure (LPEC.dll)

Object graph: `LPEC` holds {engine 0xd00 B (`FUN_100065b0`), wrapper 0x3a0 B (`FUN_10004c50`), pump 0x540 B (`FUN_10003a80`, vtable `0x100469e0`), encoder-pump 0x540 B (vtable `0x100469c0`)}. `Decode(out,in,n)` copies the input pointer/count into pump +0x538/+0x53c, clears +0x404, calls pump vtable+0x14 (= `FUN_1000ee10` **input refill**: copies n bytes into pump+4, stores count at +0x40c), then `FUN_100059e0(wrapper,out)`.

Per call of the core `FUN_10005040`: (1) pump vtable+8 (`FUN_1000f0b0`) resets byte position; (2) `FUN_1000ef20(pump,2)` reads the frame type; (3) type 0 reads 1 bit (block class) then, per subframe (2 of them), 1 bit presence + if set a 7-bit page index; the page pointer = `idx*0x40 + state+0xc8` into the F-48-inventoried page tables (state +0xcc family: 0x100390d0 16k / 0x100394d0 8k); presence 0 installs the empty-page marker `&DAT_10046a00`; (4) `FUN_10004960` builds the excitation from the selected pages, `FUN_1000f430`/`FUN_1000f1c0` apply windowing/overlap-add with the mode window (`DAT_10049f7c`: 0x1004f840 8k / 0x100628a0 16k, copied to state+0x150 for (order*8+8) bytes) into the double buffer at wrapper+0x380; (5) history slides (wrapper+0x384, order*8 bytes); (6) the frame's remaining bits are consumed by a final `FUN_1000ef20(n_rest)` with per-type budgets at wrapper +0x1c/0x20/0x24/0x28; (7) `FUN_100059e0` rounds/clips doubles to PCM16 (saturate at 0x7fff/0x8000).

Bit pump byte order: `FUN_1000ef20(pump,n)` accumulates `(byte & (0xff >> pos)) >> (8 - pos - n)` with byte index at pump+0x404 and bit-in-byte at pump+0x410 — **MSB-first packing**, matching F-47's dense-bit-packing evidence. Type 1/2/3 paths synthesize degraded/CNG frames from held state (+0x8c table, single-block variants). `SetParams FUN_10003e60` computes the per-type budgets (nominal N, 0.75x = N*3/4, 1.25x = N*5/4) and engine params (+0x2c=8/10, +0xa4=10/16, +0xac=6, +0xb0=3/4; 6000-bps special case local_30=0x20, param_2=0xdac).

## CUnitter* framing formulas (STVoice.dll, from code)

RTTI classes: `CUnitter` base + `CUnitterLpecSp`, `CUnitterLpecLp`, `CUnitterAtx96/64/48/24/16`, `CUnitterTrc/TrcLp/TrcHq`. Base vtable slot 7 (per-class override) is the frame-size selector `f(mode_byte & 0xC0)`:

| class | 0x00 | 0x40 | 0x80 | 0xC0 |
|---|---|---|---|---|
| CUnitterLpecLp | **48 B** | 36 B | 60 B | 48 B |
| CUnitterLpecSp | **128 B** | 96 B | 160 B | 128 B |

SP/LP ratio is exactly 8/3 in every mode. Base-class `FUN_1001aa81` walks packet headers (`Ordinal_15` = be16 at +4; ==0x400 means 10-byte header consumed) — independent confirmation of F-47's packet header model. Base slot 9 rounds `x` up to a 1024-multiple (packet/unit sizing). Mode helpers: Sp `v10(x,y)=x*4*y/3`, `v11(x)=x*2`; Lp `v10(x,y)=x*4*y/3`, `v11(x)=3*x/4` (conversion helpers; exact operand semantics not pinned this pass).

**MSV 16k resolved: 128 B/frame** at 15.625 fps = 16000 bps exact — F-47's leading hypothesis, now from code.

## Prototype status

`results/format-re/lpec-census/lpec_decoder.py` (stdlib-only) parses the container, emits per-frame {type, block, subframe pgidx[]}. Validation:

- **07011600.MSV (LPEC SP 16k)**: 21 packets, continuous 1024-bit grid gives **exactly 159.0 frames**; type hist {0:153, 2:3, 1:2, 3:1} — 96.2% speech frames, a coherent stream, not noise. pgidx (89 present): min 4, max 124, mean 67.5, all inside the 7-bit range. Layout CONFIRMED for SP.
- **budgtele.dvf (LPEC LP 6k)**: per-packet reset grid (21 frames x 2392 packets + 14) = **50246 frames**, matching 1014=21x48+6; continuous-384 model gives 50545.75 (non-integral — LP cannot be a pure straddling stream). On the 21-per-packet grid the leading 2-bit field is near-uniform ({0:18014, 1:11357, 2:10143, 3:10732}) — the LP bit layout is NOT confirmed by this field test; either LP frames do not start with the same 2-bit type, the grid phase differs, or LP mixes per-type bit budgets (0.75x/1.25x) on a variable-length schedule. Honest negative.

## Honest negatives

- LP-mode (6 kbps) frame bit layout not confirmed; the SP layout does not transfer verbatim. Next lever: decompile `FUN_10004960`/`FUN_10005ca0` and trace every `FUN_1000ef20` call to close the bit-accounting per type.
- Lag (pitch) extraction not achieved this pass: no direct lag field was observed at frame level in the type-0 reads; lag is likely embedded in the selected codebook page rows (page = idx*0x40 bytes into the +0xcc tables) or read inside `FUN_10004960` — open.
- CELP synthesis (excitation->speech) not implemented; the prototype is a frame/parameter parser. LPC synthesis filter coefficients (`FUN_1000f430` + LSF table `DAT_10049bb0`) not decoded.
- v10/v11 helper semantics (samples-vs-bits operand order) unpinned; per-type budget bit-vs-sample units ambiguity in the core's final skip noted.
- No full-file PCM output; spectral validation therefore not possible yet (only structural plausibility checks above).

## Next levers (named)

1. Decompile `FUN_10004960` (excitation) + `FUN_1000f430`/`FUN_1000f1c0` (filter/window) and enumerate all `FUN_1000ef20` widths per type — closes LP layout and likely exposes lag fields.
2. Extract table rows at +0xcc/+0xd4/+0xd8 (page tables) and correlate pgidx distributions with pulse patterns (VSELP-style fixed codebook hypothesis).
3. Re-encode Rosetta: run Sony's encoder (LPECEncoder::InitEncoder/Encode, already mapped in F-48) under Wine on a known WAV to get frame-aligned known-plaintext.
