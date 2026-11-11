# Hexagon decode unlocked: Ghidra 12.2 headless decode-verification of the F-23 WMI handler pointers (F-28)

**Finding:** Hexagon disassembly capability is now installed and working on this host
(Ghidra 12.2 PUBLIC, language `Hexagon:LE:32:default` — "Qualcomm Hexagon V69 processor
(QDSP6) 32-bit little-endian", the correct ISA for QCA6750/wpss; wpss.mdt e_machine=164
per F-23). Using it, the F-23 per-group WMI handler mapping in `wpss.b06` was
decode-verified: the dominant per-group registry pointers **disassemble as real,
coherent Hexagon code and accept function creation at 21 of 22 sampled addresses**, and
all 28 eh_frame-verified function starts become functions. First decoded cross-references
from b06 code into b09-resident data were also captured. Per the prior-art audit
(results/prior-art-audit.md) no published decode-level analysis of these images exists —
these results are first.

## Claim

1. **Capability:** Ghidra 12.2 headless + Hexagon processor module runs on this host.
   wpss.b06 imports at base 0xc0002000 (b06 phdr vaddr, filesz 6,074,641 = exact file
   size) as one flat block `ram:0xc0002000-0xc05cd110`.
2. **Decode-verification (load-bearing):** all four dominant per-group handlers decode:
   PDEV 0xc02cd9cc (function body **9,828 B**; serves 48 PDEV-group records under F-22's
   strict filter / 47 under F-23's loose filter), VDEV 0xc031d8c8 (37, 3,864 B),
   ROAM 0xc035d2e0 (22, 88 B), PEER 0xc02d94bc (20, 60 B); plus 17 more F-23 pointers
   (full table in results/hexagon-decode.json). The one F-23-flagged anomaly, the ODD
   pointer 0xc04ecc3d, produced NO instruction and NO function at decode level —
   Hexagon packets are 4-byte-aligned; F-23's suspicion is confirmed.
3. **eh_frame ground truth:** 28/28 FDE starts (0xc04e6878–0xc04e7a70) take functions
   (bodies 4–1,032 B). F-22/F-23's "RV32-C noise at eh_frame starts" is positively
   resolved as wrong-ISA decode: the same addresses decode as real Hexagon instructions.
4. **First decoded b06→b09 references:** code at 0xc0146404–0xc0146468 builds absolute
   addresses `0xc0682340`/`0xc0682348` via immext constext pairs (`assign R3,##0xc0682348`,
   `memh (##0xc0682340),R2.L`, `memuh R2,(##0xc0682340)`) — inside b09 phdr range
   0xc0667000–0xc06c4000 and inside the F-22 window 0xc0682000–0xc06a0000. The PDEV
   handler itself decodes with `memw.if(P0) R2,(##0xc06bde64)` — also b09-resident
   (beyond the registry window). F-23's consumer-constant-search negative is overturned
   at decode level; whether any reference targets the F-22 record registry 0xc0691080+
   specifically is NOT yet established (scan partial, see negatives).
5. **Decompiler:** DecompInterface launches but all 4 big handlers failed with
   decompiler-process timeouts (60 s each) on this load-heavy host — decompiler support
   for Hexagon remains unproven here; disassembly is fully working.

## Install notes (honest log)

- Ghidra 12.2 (`ghidra_12.2_PUBLIC_20261016.zip`, 569,712,708 B). Attempt 1: **404** —
  asset filename guessed from the release *date* (20261022); the zip is stamped with the
  *build* date (20261016), which the release API lists. Attempt 2 with the correct URL
  succeeded first try (wget -c, ~1 MB/s; the dexvert-era flakiness did not reproduce).
- **SHA-256 verified** against the release page:
  `2c2cd776db3c1f6a097ba418922378ac3649cadd5e844a6f5f088ae628a7be67` (match).
- Java: host had JRE 21 only (no `javac`). Ghidra 12.2 requires **Java 25** — JDK 21 was
  rejected ("unsupported java version"). Adoptium/Temurin JDK 25.0.5+8 tarball
  (207,858,352 B) installed via JAVA_HOME. (A JDK 21 tarball was fetched first, unused.)
- Launcher gotchas, documented to save the next agent the same hour:
  - Ghidra rejects project paths with any dot-prefixed path element — the workspace lives
    under `~/.zcode/...`; inputs were copied to `/tmp/f26/`, project in `/tmp/f26/ghidra-proj/`
    (parent dir must pre-exist).
  - `-loader RawBinaryLoader` / `"Binary Loader"` / `"Raw Binary"` all fail ("Invalid loader
    name") despite the loader's `getName()` returning "Raw Binary"; omitting `-loader`
    entirely works (default loader for unknown formats IS Raw Binary) and
    `-loader-baseAddr 0xc0002000` still applies.
  - Working command: `analyzeHeadless /tmp/f26/ghidra-proj wpssproj -import /tmp/f26/wpss.b06
    -processor Hexagon:LE:32:default -loader-baseAddr 0xc0002000 -analysisTimeoutPerFile 300`
  - PyGhidra 3.2.0 (bundled wheel, `pip install --user --break-system-packages`) + Jpype
    1.7.1 drives the saved project from CPython: `GhidraProject.openProject("/tmp/f26/ghidra-proj",
    "wpssproj")` takes a String path (not java.io.File). Ghidra 12.2 API notes:
    `MemoryBlockUtils` is in `ghidra.app.util`; `Listing.getCodeUnitAt/getInstructionAfter`
    take `Address`, not `Instruction`.
- Ghidra/JDK stay out of git (no binaries to the repo).

## Method

1. F-23 targets: 22 handler pointers (14 top_ptrs + group-table secondaries incl. odd
   0xc04ecc3d), 28 eh_frame FDE begins, 30 registry run heads, 179 registry record ptr fields.
2. For every address: explicit `DisassembleCommand` (follow-flow) + `CreateFunctionCmd`;
   recorded first instruction, function creation, function body size. Program saved.
3. Planned but failed: wpss.b09 as initialized memory block at 0xc0667000 (API overload
   mismatch — registry→handler data xrefs not built this pass).
4. Constant scan: instruction operand scalars/addresses in registry window
   0xc0682000–0xc06a0000 (120 s budget, partial: 150k instructions); raw 32-bit-word scan
   of the b06 file for window values (complete: 33 hits).
5. Decompile attempt on the 4 big handlers.

## Decode-verification results

| pointer | group(s) | records | Hexagon decode | function | body B |
|---|---|---|---|---|---|
| `0xc02cd9cc` | PDEV(4)+MGMT/SUSPEND(17) | 47 | yes | yes | 9828 |
| `0xc031d8c8` | VDEV(5) | 37 | yes | yes | 3864 |
| `0xc02d94bc` | PEER(6) | 20 | yes | yes | 60 |
| `0xc035d2e0` | ROAM(11) | 22 | yes | yes | 88 |
| `0xc0377b5c` | BA_NEG(8) | 5 | yes | yes | 88 |
| `0xc03bd4c0` | MGMT(7) | 5 | yes | yes | 2216 |
| `0xc02df240` | MGMT(7) | 4 | yes | yes | 336 |
| `0xc0376c54` | DFS(10) | 4 | yes | yes | 104 |
| `0xc03771b8` | DFS(10) | 4 | yes | yes | 1212 |
| `0xc03c1ca8` | P2P(13) | 2 | yes | yes | 4956 |
| `0xc03d3640` | P2P(13) | 2 | yes | yes | 2848 |
| `0xc04b603c` | PROFILE(16) | 4 | yes | yes | 4932 |
| `0xc04ecc3d` | PROFILE(16)+SUSPEND(17) | 4 | NO | no | - |
| `0xc03b9be8` | BCN_FILTER(18) | 2 | yes | yes | 412 |
| `0xc0424740` | WOW(19) | 3 | yes | yes | 4208 |
| `0xc03cffa0` | WOW(19) | 2 | yes | yes | 1668 |
| `0xc0400550` | RTT(20) | 2 | yes | yes | 352 |
| `0xc017612c` | ? | 2 | yes | yes | 904 |
| `0xc02df400` | ? | 2 | yes | yes | 2164 |
| `0xc02f2f20` | SCAN(3) | 1 | yes | yes | 2316 |
| `0xc02f382c` | SCAN(3) | 1 | yes | yes | 92 |
| `0xc02f3888` | SCAN(3) | 1 | yes | yes | 368 |

Prologue shapes observed across the pointer set: `bitsplit` packet-bit extraction,
`call <stub>` + `allocframe` sequences, `immext`+`combine/assign` absolute-pointer pairs,
`and Rx,Ry,#-0x100` id-extraction, and cmp/jump dispatch trees. Internal coherence check:
VDEV/PEER/ROAM/BA_NEG/SCAN handlers begin with `call 0xc04e6098/0xc04e60f0/0xc04e60cc` —
a shared stub cluster adjacent to the eh_frame function-start region (0xc04e6878+).

## Hexagon listing excerpt: 0xc02cd9cc (PDEV dominant handler, first 30 packets)

```
c02cd9cc  bitsplit R5R4,R1,#0x8 
c02cd9d0  call 0xc04e60cc 
c02cd9d4  allocframe #0xd8 
c02cd9d8  immext #0x10000 
c02cd9dc  combine R17R16,##0x10000,R2 
c02cd9e0  immext #0xc056c900 
c02cd9e4  assign R18,##0xc056c90b 
c02cd9e8  cmp.gt P0,R5,#0x15f 
c02cd9ec  jump.if(P0) 0xc02cdaec 
c02cd9f0  cmp.eq P0,R5,#0x40 
c02cd9f4  add.if(P0.new) R2,R4,#-0x1 
c02cd9f8  jump.if(P0.new):nt 0xc02cdb8c 
c02cd9fc  cmp.eq P0,R5,#0x50 
c02cda00  jump.if(P0.new):nt 0xc02cdc80 
c02cda04  cmp.eq P0,R5,#0x110 
c02cda08  jump.if(!P0.new):nt 0xc02cedcc 
c02cda0c  cmp.eq P0,R4,#0x1 
c02cda10  immext #0xc0bad800 
c02cda14  assign R20,##0xc0bad838 
c02cda18  memw.if(P0) R19,(R16) 
c02cda1c  immext #0xc06bde40 
c02cda20  memw.if(P0) R2,(##0xc06bde64) 
c02cda24  jump.if(P0) 0xc02cdcd4 
c02cda28  immext #0x1c0 
c02cda2c  memw.if(P0) R17,(R2+##0x1e8) 
c02cda30  immext #0x1380 
c02cda34  cmp.eq P0,R4,#0x2 ; jump.if(!P0.new):nt 0xc02cedcc 
c02cda38  assign R1,#0x0 
c02cda3c  combine R3R2,#0x0,#0x0 
c02cda40  memw R0,(R20) 
```

Read: real dispatcher code — `bitsplit` extracts packet/loop bits; `allocframe #0xd8`
allocates a large frame; `cmp.eq P0,R5,#0x40/0x50/0x110` / `cmp.gt P0,R5,#0x15f` /
`cmp.eq P0,R4,#0x1/0x2` form an event-ID dispatch tree with predicated jumps
(`jump.if(P0.new):nt`); immext pairs materialize absolute pointers (0xc056c90b, 0xc0bad838
in-b06; **0xc06bde64 in b09**).

## What this settles

- F-23 `handler_prologue_validity: "not verifiable: no Hexagon disassembler on host"` —
  resolved: the pointers ARE Hexagon code (21/22), with the odd pointer confirmed dead.
- Per-group handler mapping upgraded from "structural only" to "decode-verified at the
  dominant pointer per major group" (PDEV/VDEV/PEER/ROAM + BA_NEG/DFS/MGMT/P2P/PROFILE/
  BCN_FILTER/WOW/RTT).
- The lab's #1 capability gap (F-23) is closed: Hexagon decode is repeatable on this box
  (tools kept under tools-ghidra/ in the workspace, not in git).

## Honest negatives / limits

- Full auto-analysis timed out at the 300 s cap; program saved with partial analysis.
  All verification is seeded by explicit disassembly at target addresses, so verdicts
  do not depend on auto-analysis.
- b09 memory-block add failed (MemoryBlockUtils overload mismatch) — registry→handler
  data-reference graph not built this pass; retryable with the documented 13-arg overload.
- Constant scan partial (150k instructions, 120 s budget, stopped early; flat program
  holds ~1.4M potential packets). The 0xc0146404 code region was covered; the
  0xc04e-0xc057 region shows 33 raw window-valued words (e.g. 0xc04e9a54: 0xc069f000,
  0xc054074c: 0xc068ac28, and **0xc057a518–0xc057a530: 0xc0692cd0/0xc0692d00/0xc0692d18/
  0xc0692dc0 — values landing between the F-23 registry runs 0xc0692a30/0xc0692aa0 and
  0xc06934a8**) that need instruction-level confirmation before counting as decoded refs.
- No sampled constant equals the F-22 record registry area 0xc0691080+ specifically yet.
- Decompiler timeouts on all 4 big handlers (60 s each) — Hexagon decompiler support
  unproven on this host; retry with longer timeout on an idle box.
- The odd pointer 0xc04ecc3d: disassemble command applied, but no instruction/function
  produced — consistent with 4-byte packet alignment; its 4 PROFILE/SUSPEND registry
  records likely point at data or a mis-recorded pointer.

## Repro pointers

- Kept on host (out of git): tools-ghidra/ — Ghidra 12.2 install, jdk-25, scripts/hexagon_verify.py,
  targets.json, decode-results.json (full), pdev-listing.json, headless logs
  (headless-import*.log, verify-run*.log, dump-listing.log). wpss.b06/b09 copies at /tmp/f26/.
- Raw results: track-a-android-blobs/results/hexagon-decode.json (this doc's numbers).
