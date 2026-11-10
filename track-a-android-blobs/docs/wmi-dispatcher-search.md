# WMI dispatcher search: runtime ID-construction sites in WCN6750 wpss firmware

**Claim:** First full linear-sweep disassembly of the WCN6750 `wpss.b07` program
segments (RV32+C) and the first targeted search for WMI message-ID construction
sites (`grp<<12|1`-style arithmetic). Result: **no construction site exists in
`wpss.b07`** — the two pure-code LOADs decode at 100.0% coverage (24,030
instructions) and contain no `slli×12` feeding an `ori/addi 1`, no
`lui+addi` materializing any ID-shaped constant (`(v & 0xFFF)==1` in
`[0x1001..0xFF001]`), and no ID tables at 4-byte or 2-byte granularity. The
five `slli a?, a?, 12` sites in the code are **packed-pointer indexing**
(`(w<<12) + base`, then dereferenced as an address), not ID arithmetic. A new
16-bit halfword scan (202 candidate IDs) is quantitatively at chance level and
is deflated by the adsp.b36 negative control, extending F-19's deflation to
halfword granularity. Nothing about this search exists in public literature
(GitHub code/repo search, checked 2026-11-11).

## Method

- Tool: `wpss_disasm.py` extended into a sweep+pattern scanner (capstone
  5.0.7, `CS_MODE_RISCV32|CS_MODE_RISCVC`): per-PT_LOAD linear sweep with
  resync (on undecodable bytes skip 2 and retry), constant propagation over
  the instruction stream, and a value scanner restricted to LOAD ranges.
- Segment ground truth from the ELF32 program headers themselves (struct
  parse) — which **corrects the F-5 task brief**: wpss.b07 has **6 PT_LOADs**,
  not 3 (details below). A constant-propagation self-test (synthetic
  `lui+addi→0x3001`, `c.li+c.slli+c.ori→0x3001` chains) confirms the tracker
  catches every searched construction form before trusting negatives.
- Patterns searched on the decoded stream:
  - **A1:** every `slli`/`c.slli` with shift==12 (catch-all, no tracking).
  - **A2:** `lui`/`c.lui` of a group immediate (1..254) followed by
    `addi`/`ori` of 1 on the same register (assembler-folded `li grp<<12|1`).
  - **A3:** any tracked constant materialization with value in
    `[0x1001..0xFF001]` and `(v & 0xFFF)==1` (any construction path).
  - **B:** aligned LE32 scan of the 605 ath11k IDs (via `xref_wmi.py`)
    restricted to LOAD file ranges vs whole file (F-9 comparison).
  - **B′ (new):** 2-byte halfword scan of the same IDs + adjacency-run test
    (≥6 consecutive ID halfwords = table signature) + adsp.b36 control.
  - **C:** wpss.b08 disassembled from offset 0.

## Decode coverage (the first published numbers for this firmware)

| wpss.b07 PT_LOAD | file off | vaddr | filesz | decoded | coverage | insns | profile |
|---|---|---|---|---|---|---|---|
| 0 | 0x4000 | 0x404000 | 2,330 | 2,330 | 100.0% | 915 | entry code (424 `c.unimp` = zero pad) |
| 1 | 0x4a00 | 0x404a00 | 66,264 | 66,262 | 100.0% | 23,115 | clean code (`c.li/addi/lw/jal/c.swsp`) |
| 2 | 0x14d80 | 0x404d80 | 8 | 8 | 100.0% | 4 | pad |
| 3 | 0x18cd8 | 0x414cd8 | 20,724 | 19,350 | 93.4% | 9,290 | mixed; top decode is `c.unimp` (5,644) → data-heavy |
| 4 | 0x1ddd0 | 0x419dd0 | 0 | 0 | — | 0 | BSS (filesz 0) |
| 5 | 0x1e528 | 0x422528 | 14,385 | 13,022 | 90.5% | 5,738 | rodata; decode dominated by `c.flw/c.lui` noise |

Pure-code LOADs (0,1,2): 68,602 B at **100.0% coverage**, 24,030 instructions.
All LOADs: 103,711 B, 100,972 B decoded (97.4%). The 93.4%/90.5% segments
decode "validly" only because RV32C has almost no invalid encodings — their
mnemonic profile (`c.unimp`, `c.flw`) is the data signature, not code.

## Results

### Pattern A — construction sites: none in clean code

- **A1 (`slli×12`):** exactly **5 sites in all of wpss.b07 code** (all in
  LOAD 1): 0x405872, 0x4119a2, 0x4119ae, 0x4120fa, 0x412118. Every one is
  packed-pointer addressing: a word is loaded from a table/struct
  (`c.lw a3, 8(a1)` …), shifted 12, added to a running offset (`c.add a3, a2`,
  with `a2` incremented by 4 per step), and **dereferenced** (`c.lw a3, 0(a3)`)
  or used as a store address. Example (0x4119a2):
  `c.lw a3,8(a1); c.addi a2,4; c.slli a3,0xc; c.add a3,a2; c.lw a3,0(a3);
  c.andi a3,3`. None of the 5 feeds an `ori/addi` of 1 that would produce a
  WMI ID.
- **A2/A3 (materialized ID-shaped constants):** **zero hits in 24,030
  clean-code instructions**. The ~120 `lui <small-imm>` shapes in LOAD 1 (e.g.
  `lui a0,0x1` = `li 0x1000`) are ordinary address/size constants; none is
  followed by `addi/ori rd, rd, 1` on the same register. Data segments and
  b08 produce hundreds of such "shapes" when interpreted as code — a pure
  false-positive class, reported for completeness in the JSON.
- The ISA machinery for `grp<<12|k` demonstrably exists in this codebase (the
  5 packed-pointer sites) — it is simply not applied to WMI IDs.

### Pattern B — word-aligned literals, in-range vs whole file (F-9 comparison)

- wpss.b07: 6 hits / 3 values in-range == 6 / 3 whole-file. F-9's b07 word
  hits sit entirely inside LOAD ranges (none in padding). b08 = 20 hits /
  9 values in-range vs 22 / 10 whole-file; the two excluded hits are exactly
  the artifacts: `0x30002` @ 0x10 (the junk ELF header F-9 flagged) and one
  `0x10003` @ 0x4101c in the 8 KB tail beyond the 262,144-byte LOAD. So the
  F-9 word-level numbers were already pad-free except those two entries, and
  the profile-cluster region (0xb58c–0xbd2c) lies inside the LOAD.

### Pattern B′ — halfword scan (new evidence class; deflated by control)

| segment | size | hw hits | distinct values | per-KB | ≥6-run tables |
|---|---|---|---|---|---|
| wpss.b07 | 139,316 | 246 | 39 | 1.8 | 1 (the 0xa001 DFS fill at 0x438e, matching F-9) |
| wpss.b08 | 275,644 | 4,034 | 176 | 14.6 | **0** |
| adsp.b36 (control) | 6,386,356 | 171,574 | **202/202** | 26.9 | **0** |

The control reproduces and exceeds everything: all 202 distinct 16-bit ID
values appear in unrelated Hexagon audio-DSP firmware at a higher per-KB rate.
wpss.b08's distinct-value count (176) matches the chance expectation for
131,072 halfword positions over 202 candidates (≈175) to within 1; its
hit-count excess (10× chance) comes from repeated data patterns (0x6001 ×529,
0x6008 ×319) — the same skew the control shows. **No contiguous ID table
exists at 2-byte granularity anywhere.** This extends the F-19 deflation
(word granularity) to halfwords.

### Pattern C — wpss.b08 as hidden code: negative

275,644 B disassembled from offset 0: 113,728 decodes, 92.0% byte coverage —
but 37,568 (33%) of decodes are `c.unimp` (all-zero halfwords) and the top
real mnemonics are FP-store/load noise encodings (`c.fsw` 14,227, `c.fld`,
`c.flw`). This is a data segment whose zeros and structured words happen to
be valid RVC encodings, **not** hidden code; the junk e_machine header (F-7)
concealed nothing.

## Verdict

**No WMI ID construction site exists in wpss.b07**, and no WMI ID table
exists in b07/b08 at 4-byte or 2-byte granularity. F-9/F-19's structural
conclusion ("IDs computed at runtime as grp<<12|1") is now **falsified in its
specific mechanism** for wpss.b07: the computation pattern is absent from
100%-coverage code. What survives is stronger: in this firmware image the WMI
ID space appears to be neither stored nor constructed. Plausible remaining
explanations (ranked): (1) firmware-side dispatch keys on message contents /
HTC endpoint routing, with numeric IDs used only host-side; (2) the
dispatcher lives in an unexamined wpss segment (b09/b10/b12 are present in
the image tree and untouched by this search); (3) construction via a form
outside the searched set (e.g., group bytes fetched from arrays with the
shift folded into a register-indirect addressing path my sweep cannot track
across function boundaries). The packed-pointer idiom found here
(`(w<<12)+off` tables) is the codebase's native computed-indexing style and a
concrete template for what a dispatcher table would look like.

## Honest negatives

- 100.0% coverage claim applies to LOADs 0–2 only; LOADs 3/5 are 93.4%/90.5%
  (data regions inside mixed segments decoded as "instructions" inflate
  apparent pattern counts — construction hits there are meaningless noise and
  are labeled as such in the JSON).
- Constant propagation is window-local; a construction split across a call
  boundary (group in a callee-saved register) would be missed by A2/A3, but
  A1's catch-all bounds this: any `grp<<12` arithmetic must contain a
  `slli×12`, and there are exactly 5, none ID-shaped.
- Jump tables via `jalr` with base+offset were not exhaustively enumerated;
  the 5 packed-pointer sites are the visible examples of that idiom.

## Prior art

None. GitHub code search (`"wpss.b07" disassembly`, `qca6750 wpss firmware
riscv disassembly`, WMI-construction patterns) and repo search return zero
results (checked 2026-11-11). This is the first public full-coverage
disassembly census of the WCN6750 wpss program segments and the first search
for runtime WMI-ID construction.
