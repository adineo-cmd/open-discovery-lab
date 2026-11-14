# Sony LPEC reference DLLs obtained and statically analyzed — codec API, CELP-family confirmation, per-mode codebook inventory (F-48-or-next-free)

Date: 2026-11-14. Direct continuation of F-47 (bitstream structural first pass). This session crosses the boundary F-47 documented but did not cross: the Windows-only reference implementation is now located, extracted, and analyzed at static-census level in Ghidra. The LPEC codec interior is no longer unknown at the structural level — it is a CELP-family analysis-by-synthesis codec with per-mode fixed-point codebook tables, and its complete public API is mapped. The frame-size question for MSV 16000 stays open (frame sizes are not hardcoded in the codec core; they live in the container-layer DLLs). Honest negatives included.

## Claim

The LPEC codec reference implementation is a 32-bit x86 C++ DLL (LPEC.dll, 329,064 B, 402 functions) shipping inside Sony Digital Voice Editor installers, exporting a clean class API (`LPEC::InitCodec(int,int,int)`, `LPECDecoder::Decode(unsigned short*, char*, int)` — PCM out as shorts, bitstream in as chars). Static analysis confirms: (1) mode selection is by sample rate (8000/16000 Hz sets) with bitrate 6000 bps special-cased inside the 8000 Hz set — matching F-47's LPEC 6000 bps variant arithmetic; (2) the codec is CELP-family (per-frame diagnostic string reports `lag` and `pgidx` — pitch lag and codebook page index); (3) the complete per-mode codebook table inventory is extracted: ~15 table pointers per mode, 512 B to 33 KB each, signed 16-bit fixed-point values, installed at fixed decoder-state offsets. Frame sizes 24/48/128 (F-47) appear NOWHERE as immediate constants in LPEC.dll — codec framing is computed in the container-layer DLLs (STVoice.dll/PVoice.dll `CUnitter*` classes), so the MSV 16000 {24,48,128} question is handed to the next lever, now precisely named.

## Provenance (full chain, no Sony binaries committed)

- Container: Sony Digital Voice Editor Ver. 3.3.01 (ICD-PX820 CD-ROM; internal file dates 2009-11-24). Downloaded from archive.org item `dve3301icdpx820`, file `DVE_3301 ICD-PX820.iso` (112,668,672 B). The live Sony page (sony.com W0001286 ICS Converter) is JS/bot-gated (403 to fetchers) — archive.org was used instead; the F-47-named PVoice.dll/STVoice.dll ship inside DVE, which supersedes ICS Converter.
- ISO extracted with 7zz 26.06 (static binary from the ip7z/7zip GitHub release; 7-zip.org is 404-blocked from this egress).
- Payload: InstallShield v6 cabinets `Setup/DVE/data1.cab` (10,900,003 B, `ISc(` magic) + `data1.hdr`. No 7zz/`cabextract` support; built `unshield` from source (github.com/twogood/unshield, plain gcc + zlib, minimal config header) — recorded here to save the next agent the build.
- Ten codec binaries extracted (all PE32 i386, machine 0x14c; sizes exact): `System\LPEC.dll` 329,064 B; `DefaultComponent32bit\STVoice.dll` 669,032 B; `DefaultComponent32bit\SXVoice.dll` 689,512 B; `WMF\PVoice.dll` 693,608 B; `WMF\BPVoice.dll` 591,208 B; `System\dsp_trc.dll` 81,920 B; `DirectShowFilter\lpecde.ax` 69,632 B; `trcde.ax` 69,632 B; `msvdec.ax` 102,400 B; `WMF\msvtrcw.spi` 122,880 B. **None committed to git** (lab policy: derived facts only).
- Tooling: Ghidra 12.2 PUBLIC headless via PyGhidra (JDK 25.0.5+8), `x86:LE:32:default`; LPEC.dll fully analyzed (402 functions), msvdec.ax analyzed (718 functions); capstone x86-32 for targeted disassembly. Note for the next agent: headless `analyzeHeadless` + `.py` postScript fails with "Ghidra was not started with PyGhidra" — use the `pyghidra` Python API (works).

## Method

Static only, no execution, no Wine. Pass 1: Ghidra auto-analysis + symbol/string extraction + per-function immediate-constant census (bitrates 6000/16000/19200, sample rates 8000/11025/22050/32000/44100, packet constants 1024/1014) + imul/mul/lea factor census for frame sizes {24,48,128,192,384}. Pass 2: targeted decompilation of the API entry points and the constant-hit functions. Pass 3: codebook table sizing by address-delta arithmetic over the table-pointer sets installed by the mode-dispatch function. Everything below is derived fact; no decompiled code is reproduced.

## Findings

### 1. LPEC.dll public API (all facts from Ghidra symbol table + decompiler)

- 22 named exports (65 export entries incl. ordinals), MSVC C++ classes, demangled:
  - `int LPEC::InitCodec(int,int,int)` @ VA 0x10002f20 — allocates and wires 4 sub-objects: state 0x540 B, engine 0xd00 B, decoder 0x540 B, wrapper 0x3a0 B.
  - `int LPEC::Decode(unsigned short* out, char* in, int count)` @ 0x100032b0 — **PCM out is u16 shorts, bitstream in is raw bytes**: the exact codec I/O boundary for a reimplementation.
  - `int LPEC::Encode(char*, unsigned short*, int)` @ 0x10003950; `ResetDecoder/ResetEncoder`; `getEncBlockSize()`.
  - `LPECDecoder::InitDecoder(int,int)` @ 0x100035e0, `LPECDecoder::Decode(unsigned short*, char*, int)` @ 0x10003820.
- Decode flow: input pointer/count stored in decoder state (+0x538/+0x53c, input position at +0x404 cleared), virtual call at vtable+0x14 = the bitstream pump, then wrapper function FUN_100059e0 synthesizes the PCM. `Decode(out, NULL, 0)` zero-fills the output buffer — silence is generated PCM zeros at this level (consistent with F-47: no deterministic silence code in the bitstream).
- `InitCodec` first parameter behaves as a **sample rate**: ≤11025 → 1024-byte buffer; 11026–22050 → 2048; ≥22051 → 4096 (thresholds 0x2b12/0x5623). `this+0x10` = bytes/2.

### 2. Mode selection — the bridge to F-47's bitrates

- Engine init FUN_10003e60 (called from InitCodec chain): sample rate < 0x1f41 (8001) sets decoder-state fields {+0x2c: 8, +0xa4: 10, +0xac: 6, +0xb0: 3}; rate 8001–32000 sets {+0x2c: 10, +0xa4: 16, +0xac: 6, +0xb0: 4}; state+0xa8 = 1<<6. Rate > 32000 → error string `Invalid FS %d`.
- **Bitrate 6000 special case**: `0 < bitrate < 0x1771 (6001)` triggers a distinct branch (`0x20`, param 0xdac) — this is F-47's LPEC 6000 bps variant (budgtele/STVoice) being explicitly parameterized in the codec core.
- Mode-table dispatch FUN_1000df10: two complete table-pointer sets — **16000 Hz set** vs **8000 Hz set**; inside the 8000 set, **bitrate 6000 selects a specific table pair** (`0x100388b0`/`0x10038cb0`) vs other bitrates (`0x10038cc0`/`0x100390c0`). Interpretation (census-level, clearly labeled): param_1 = sample rate in Hz, param_2 = bitrate in bps; the 16000 Hz set is the ICD-BM1 MSV-class mode, the 8000 Hz set covers the ST/BP-class SP/LP modes.

### 3. Codec family confirmation: CELP, not ADPCM

- Diagnostic string at 0x1006b54f: `Error in frame %d(lag = %d, pgidx = %d)` — per-frame decode errors report a **pitch lag** (long-term prediction) and a **codebook page/grid index** (fixed excitation codebook). This is analysis-by-synthesis CELP-family structure, not ADPCM (despite "ADPCM LP/SP" mode-name strings in the container DLLs — those are the legacy ICD-P modes; LPEC SP/LP are separate).
- This explains F-47's observations: dense 7.8–7.9 bits/byte packing (vectors + codebook indices, not waveform samples), per-frame comfort noise (each frame carries fresh excitation indices), no mode byte (mode is fixed at init by rate/bitrate).

### 4. Codebook table inventory (the Rosetta target)

Per-mode pointer sets installed at fixed decoder-state offsets (sizes = address-delta upper bounds; values are signed 16-bit fixed-point, spot-checked non-trivial):

- **16000 Hz set**: 4 × 2048 B tables (0x10019040/0x10019840/0x1001a040/0x1001a840, state 0x114–0x120); 4 × 8192 B tables (0x1001b040/0x1001d040/0x1001f040/0x10021040, state 0xb4–0xc0); large table at 0x10021040 (33,792 B span); 0x10029440 (4,096), 0x1002a440 (8,192), 0x1002c440 (52,368), 0x100390d0 (7,168), 0x1003acd0 (13,312), 0x1003e0d0 (512), 0x1003e2d0 (512).
- **8000 Hz set**: 0x10023040 (1,280), 0x10023540 (1,280), 0x10023a40 (2,560); 4 × 5,120 B (0x10024440/0x10025840/0x10026c40/0x10028040); 0x10028040 span 33,792; 0x10030440 (4,096), 0x10031440 (8,192), 0x10033440 (24,720), 0x100394d0 (11,264), 0x1003c0d0 (4,096), 0x1003d0d0 (5,120), 0x1003e4d0 (512), 0x1003e6d0 (512).

Full machine-readable inventory (addresses, state offsets, sizes, sub-selection pairs) in `results/format-re/lpec-census/lpec-dll-analysis.json`. These tables ARE the LPEC codebooks — dumping them as shorts is the first step of a Python decoder prototype, but they are Sony's data and stay out of git.

### 5. Container layer (STVoice/PVoice/msvdec) — census only this pass

- The voice DLLs share the same codec-mode string set: `ADPCM LP`, `ADPCM SP`, `LPEC(for ICD-BPx20 series) LP/SP`, `LPEC(for ICD-MX series) LP/SP`, plus classes `CUnitterLpecLp`, `CUnitterLpecSp`, `CUnitterTrc`, `CUnitterTrcHq`, `CUnitterTrcHqPage`, `CUnitterTrcLp`, `CUnitterTrcLpPage`, `CUnitterTrcSpPage`, `CMetaDataMsv`, `CMsveRegistory` — the `CUnitter*` classes are per-format/per-mode framing adapters ("unitter" = unit writer/reader).
- `msvdec.ax` is a DirectShow transform filter `CMSVDecryptFilter`/`IMSVDecrypt` (`This is a MSV Format`, `MSVDEC module`) — the MSV container/transport layer, separate from the codec. Its 1024/1014 constant-census hits exist but the 1014 site decompiles as a property-page dialog proc — **weak evidence, not counted as confirmation of F-47's packet header at this level**.
- `lpecde.ax`/`trcde.ax` (69,632 B each) are the DirectShow LPEC/TRC decoder filters (lpecde links the LPEC classes; trcde is the TRC-side filter).
- **Frame sizes 24/48/128/192/384 as imul/mul/lea factors: zero hits across all of LPEC.dll.** The codec core consumes frames fed by the container; frame byte lengths are computed in the `CUnitter*` framing functions (sample-rate × bitrate arithmetic), consistent with F-47's finding that TRC 19200 = 24 B and LPEC 6000 = 48 B close the bitrate arithmetic exactly.

### 6. F-47 hypothesis status after this pass

| F-47 item | status after DLL analysis |
|---|---|
| TRC 19200 = 24 B/10 ms | arithmetic confirmed again (not directly visible in LPEC.dll; framing is container-side) |
| LPEC 6000 = 48 B/64 ms | codec core explicitly special-cases bitrate 6000 inside the 8000 Hz set — variant is real and parameterized |
| MSV 16000 {24,48,128} | still unresolved; the 16000 Hz table set exists; next lever named below |
| silence = per-frame comfort noise | consistent (Decode-NULL zero-fills; no static silence code in codec core) |
| no mode byte per frame | explained: mode fixed at init (rate/bitrate), frame = pure payload |
| dense bit packing 7.8–7.9 b/B | explained: CELP fixed-point vector/codebook indices |

## Honest negatives

- No dynamic analysis: the DLLs were never executed; all findings are static census-level. Semantics of most state fields are inferred (labeled as such), not proven.
- The bitstream pump (vtable+0x14 callee) and the PCM synthesis function FUN_100059e0 are NOT yet decompiled — the bit unpacking order (MSB/LSB-first, F-47's open question) is still not extracted.
- MSV 16000 frame size remains {24,48,128}; the CUnitter* framing functions were not decompiled this session (time bound).
- Table semantics (which table is the shape codebook vs gain vs LSP vs pitch-lag window) are not attributed — only addresses/sizes/installs mapped.
- 19200 (TRC bitrate) has no immediate hits in LPEC.dll — TRC is handled by dsp_trc.dll + trcde.ax, not analyzed this session.
- Sony binaries remain uncommitted by policy; the table contents are Sony data and are not dumped to the repo.

## Next lever (named)

1. **Decompile LPEC.dll `FUN_100059e0` (PCM synthesis) and the bitstream pump callee**: extract the bit reader (shift/mask order — MSB vs LSB first, F-47's bit-position bias question) and the per-frame field layout (lag bits, pgidx bits, gain bits). With the table inventory above, that completes the decoder spec.
2. **Decompile STVoice.dll/PVoice.dll `CUnitter*` framing functions**: compute the frame byte length formulas per (rate, bitrate) — resolves MSV 16000 {24,48,128} from code instead of statistics.
3. Dump the mode tables to local files and pair with the field layout for a Python decoder prototype (tables stay local per policy).

## Ledger TEXT (F-48-or-next-free)

> F-48-or-next-free: Sony LPEC reference DLLs obtained and statically analyzed (census level). Provenance: Digital Voice Editor 3.3.01 CD-ROM (archive.org dve3301icdpx820, 7zz + unshield-from-source chain documented); 10 codec binaries extracted, none committed. LPEC.dll (329 KB, 402 funcs) API fully mapped: LPEC::InitCodec(int,int,int), LPECDecoder::Decode(ushort*,char*,int) — PCM-out/bitstream-in boundary; mode selection by sample rate (8000/16000 Hz table sets) with bitrate 6000 bps special-cased in the 8000 set (F-47's LPEC 6k variant confirmed parameterized in the codec core). Codec family CONFIRMED CELP (per-frame diagnostic 'lag = %d, pgidx = %d' — pitch lag + codebook page index), explaining F-47's 7.8–7.9 b/B dense packing, no-mode-byte frames, and per-frame comfort noise. Complete per-mode codebook inventory extracted (15 tables/mode, 512 B–33 KB, signed 16-bit fixed-point, fixed state offsets; JSON). Frame sizes 24/48/128 not immediates in the codec core — framing lives in container-layer CUnitter* classes; MSV 16k stays open, next lever named (decompile bitstream pump + FUN_100059e0 + CUnitter framing). No binaries/decompiled code committed — derived facts only.
