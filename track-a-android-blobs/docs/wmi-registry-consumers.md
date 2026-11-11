# WMI registry consumers: the b06 side of the F-22 message-ID registry (F-23)

*Investigator: F-23, 2026-11-11. Inputs: wpss.mdt / wpss.b06 / wpss.b09
(lineage-fp6, qca6750), instruments/ath11k/wmi.h. Tooling:
scratch-wmi-dispatch/wmi_b06_consumer_scan{,2,3}.py.*

## Claim

The F-22 registry in wpss.b09 (`[ptr, id, 0]`, 12-byte stride, runs at
vaddr 0xc0691080...) is consumed by **Hexagon** code in wpss.b06 — not RISC-V
code. Two corrections and one mapping come out of this:

1. **Architecture correction (firm, header-level):** wpss.mdt declares
   `e_machine = 164 = EM_HEXAGON` (EM_ARM=40, EM_RISCV=243). b06 is a Hexagon
   QDSP image segment, not RV32+C. Every RV32-lens conclusion about b06
   executable content (F-20/F-22 "handler prologue" style tests, lui/addi
   construction search) was inapplicable; our RV32-C decodes of b06 produce
   coherent-looking noise, and they do so *even at the 28 eh_frame-verified
   function starts* — which confirms the wrong-ISA diagnosis.
2. **Per-group handler mapping (structural, high confidence):** registry
   records cluster by WMI group to ~one dominant b06 pointer per group —
   exactly the shape of per-module WMI event dispatch (one shared handler per
   pdev/vdev/peer/roam module). Mapping below.
3. **Consumer-constant search: honest negative.** No instruction encoding we
   can check (RV32 lui/auipc/addi12 over all five exec segments b01–b06; raw
   32-bit literals across b01–b12; Hexagon immext-class-0xD words) materializes
   any registry address outside b09 itself. The registry is reached via
   pointer variables (list-head anchors), not via code-materialized constants —
   or via Hexagon encodings beyond our scan's coverage.

## Method

1. Re-derived the registry from wpss.b09 independently of F-22 with a looser
   filter (ptr in b06 exec range, grp 1..20, cmd 1..0x2e0, third word 0):
   **193 records, 32 distinct pointers, of which 178 records / 26 pointers sit
   in the 30 stride-12 runs of >= 2 records** (F-22's stricter ath11k-name
   filter got 225/16; both agree on the main-run area 0xc0691080–0xc06914d8).
2. Byte-level scan of every exec segment (b01 0xfe000000, b02 0xfe002000,
   b03, b05, b06 0xc0002000–0xc05bd111 (end-exclusive; canonical per filesz 6,074,641)) for RV32 `lui`/`auipc` words landing in
   the registry window 0xc0682000–0xc06a0000, `addi rd,rd,12`, and `c.addi rd,12`;
   capstone decode of every hit context.
3. Raw 32-bit literal search for all 12 representative registry run-start
   addresses across b01–b12.
4. Hexagon immext scan: 4-byte-aligned words with top nibble 0xD whose
   26-bit field at shifts 0..6 equals `target>>6` for the 12 run starts.
5. eh_frame FDE parse of b09 (first 1072 bytes): DWARF32 FDEs with
   **absolute** pc_begin — all 28 land in b06 (0xc04e6878–0xc04e7a70),
   confirming F-22's "FDEs point into b06 ~0xC04E6BD0" and giving ground-truth
   function starts. (pcrel interpretation of the same fields yields 0x80b4xxxx,
   matching no segment — absolute is the consistent reading.)
6. ath11k cross-check: group byte of each ID against `wmi_grp` enum in
   instruments/ath11k/wmi.h; sample IDs against F-22's u32 id hit table.

## Per-group handler mapping (the load-bearing result)

| WMI grp | ath11k name | records | distinct ptrs | dominant b06 ptr (count) |
|---|---|---|---|---|
| 3 | SCAN | 7 | 7 | none dominant (0xc02f2f20, 0xc02f382c, 0xc02f3888, ...) |
| 4 | PDEV | 48 | 1 | **0xc02cd9cc (48)** |
| 5 | VDEV | 41 | 5 | **0xc031d8c8 (37)** |
| 6 | PEER | 23 | 3 | **0xc02d94bc (20)** |
| 7 | MGMT | 11 | 4 | 0xc02df240 (4), 0xc03bd4c0 (4) |
| 8 | BA_NEG | 5 | 1 | 0xc0377b5c (5) |
| 10 | DFS | 8 | 2 | 0xc0376c54 (4), 0xc03771b8 (4) |
| 11 | ROAM | 24 | 3 | **0xc035d2e0 (22)** |
| 13 | P2P | 5 | 3 | 0xc03c1ca8 (2), 0xc03d3640 (2) |
| 16 | PROFILE | 7 | 2 | 0xc04b603c (4), 0xc04ecc3d (3) |
| 17 | SUSPEND | 3 | 2 | 0xc02cd9cc (2), 0xc04ecc3d (1) |
| 18 | BCN_FILTER | 2 | 1 | 0xc03b9be8 (2) |
| 19 | WOW | 6 | 3 | 0xc0424740 (3), 0xc03cffa0 (2) |
| 20 | RTT | 2 | 1 | 0xc0400550 (2) |

Sample records (main-run area): `[0xc02cd9cc, 0x4001 WMI_PDEV_TPC_CONFIG_EVENTID, 0]`,
`[0xc02cd9cc, 0x4002 WMI_CHAN_INFO_EVENTID, 0]`, `[0xc02cd9cc, 0x4009
WMI_SERVICE_READY_EXT_EVENTID, 0]`, `[0xc02cd9cc, 0x11001, 0]`, ...; scan
records `[., 0x3001 WMI_SCAN_EVENTID, 0]`, `[., 0x3003 WMI_SCAN_CHAN_LIST_CMDID, 0]`
carry per-event pointers.

**Read:** the "ptr" column is consistent with Hexagon function pointers —
per-module dispatch handlers — with one shared handler serving a whole WMI
module's event set (PDEV 48 events → one pointer). All 32 distinct ptrs are
4-byte aligned except `0xc04ecc3d` (odd — anomalous for Hexagon packets; treat
with suspicion; it serves 3 PROFILE records + 1 SUSPEND). Registry vaddrs are
also 4-aligned, as are all 28 eh_frame function starts.

## The owner-pointer cluster 0xc02cd9cc

Inside b06 exec range (b06 = 0xc0002000–0xc05bd111 (end-exclusive; canonical per filesz 6,074,641)), 4-byte aligned, dominant
ptr of the entire registry (51 of 193 records, groups 4/5/7/17). RV32-C decode
at that address is mid-function noise (`c.lw s1, 0x10(s1)`...) — but so is the
decode at eh_frame-verified starts, so this neither confirms nor refutes
code-ness. Best supported reading: **the PDEV module's shared event handler**
(or a per-group dispatcher table entry), not a struct field — it appears only
in the ptr column, never as a standalone pointer elsewhere in b09/b10.

## List-head structure (new structural fact)

Every run start is preceded 8–12 bytes earlier by a 32-bit word equal to the
run start address itself (20 literal hits, all inside b09), e.g.
`0xc0691078: 0xc0691080`, `0xc06913dc: 0xc06913e8`, `0xc0684d94: 0xc0684da0`.
Preceding words include run record-counts (`0x14` before the 20-record run,
`0x7` before the 7-record run) and `0x1` sentinels. The registry is not one
flat table: it is a set of anchored, count-prefixed lists. Two anchored runs
sit outside the F-22 main window: 0xc0684da0 (3 recs) and 0xc069dfc8 (4 recs).

## Consumer hunt: what was checked and what it means

- RV32 lens over all exec segments: **0** lui/auipc into the registry window;
  **0** `addi rd,rd,12` in the whole 6 MB of b06 (271 `c.addi rd,12` exist but
  carry no registry linkage we can establish without a real Hexagon decoder).
- Literal search b01–b12: the registry's addresses appear **only in b09** (the
  list-head anchors) — no code or data anywhere else holds one.
- Hexagon immext-class-0xD scan: 0 hits, but the encoding assumption is
  unverified (capstone 5.0.7 ships no Hexagon decoder, so we could not
  ground-truth it). This is the main uncovered gap, not proof of absence.

## Honest unknowns

1. **No Hexagon disassembler on host** (capstone 5.0.7 lacks
   `CS_ARCH_HEXAGON`): handler prologue validity is **not verifiable**; the
   "prologue-valid 1/18" style numbers from an RV32 lens are meaningless and
   are retracted here. Next investigator needs a Hexagon decoder (llvm-objdump
   --triple=hexagon or qdsp6 objdump) to do Q2 properly.
2. Who *reads* the lists: expected to be an HTC/WMI rx dispatch loop in b06
   reached via pointer variables set up at init. Constant search cannot find
   that; needs Hexagon control-flow recovery around the anchors.
3. The 0x16010/0x1d010-style slot IDs seen before some runs (grp 0x16 = 0x16
   PROFILE, 0x1d = MISC per the ath11k enum, with cmd IDs in the low 12 bits)
   and runs 0xc0684da0/0xc069dfc8 are unmapped to ath11k names.
4. Odd pointer 0xc04ecc3d unexplained.

## Data

results/wmi-registry-consumers.json (16 KB) — full runs, cluster table,
sample decodes, FDE list, search counts. Raw scanner outputs kept in
scratch-wmi-dispatch/results-wmi-b06-consumers{,2,3}.json.

## Update (F-28/F-29, 2026-11-11/12): handler mapping decode-verified; tie-in traced

The "structural, not decode-verified" caveat and unknown #1 above are
RESOLVED: F-28 installed Ghidra 12.2 (Hexagon:LE:32:default — see
docs/hexagon-decode.md) and decode-verified the mapping — **21/22 dominant
pointers (incl. PDEV 0xc02cd9cc = 9,828-byte dispatcher) accept functions as
real Hexagon code; 28/28 eh_frame starts take functions; the odd pointer
0xc04ecc3d decodes to nothing (confirmed dead)**. F-29 additionally traced
the registry tie-in at instruction level: the PDEV dispatcher materializes
the registry head (0xc0691050/68) and arms setbit() enable masks inside the
record area — the registry is the group-routing level, per-event routing is
via b06-resident jump tables (0xc056423c / 0xc05641fc). Remaining unknowns:
per-record 12-stride consumption loop, dispatcher call-site.
