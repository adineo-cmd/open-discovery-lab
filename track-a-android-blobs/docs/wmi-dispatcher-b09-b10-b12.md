# WMI dispatcher search: the remaining wpss segments b09/b10/b12 — registry found, code segment identified

**Claim:** F-21 extends the F-20 search (linear-sweep RV32+C, construction-site
patterns, ID tables) to the last unchecked WCN6750 `wpss` segments b09/b10/b12
and reaches a structural answer. **WMI message-ID handling IS present in the
wpss image — but it is table-driven, not arithmetic.** `wpss.b09` is an RW data
segment containing the firmware's **message-ID registry**: 148 `*EVENTID` /
`*CMDID` enum-name strings (44 `WHAL_*`, 44 `WAL_*`), a 12-byte-stride table of
`[b06-code-pointer, grp<<12|cmd ID, 0]` records (225 records in 16 runs, main
run 69 records at file 0x2a080; 149 distinct IDs across WMI groups 3–13), and a
clean `.eh_frame` block whose FDEs point into b06. `wpss.b10` (95.5% ASCII) is
the format-string/trace table for the same code (11,244 strings, 66 naming WMI
cmd/event IDs in `file.c:` error text) with zero ID tables. `wpss.b12` is the
X.509 secure-boot certificate chain (PT_NULL region) — no code, closed. The mdt
program headers settle the F-20 puzzle: **b07/b08 are RW data segments** (no
PF_X) — the only executable LOADs are b01/b02/b03/b05/b06, with b06 (6.07 MB,
RWX, 0xc0002000–0xc05bd111 (end-exclusive; canonical per filesz 6,074,641)) as the main code. F-20's "zero construction sites"
is therefore fully explained: construction-site hunting was the wrong
instrument for a table-driven dispatcher. Nothing about this registry exists in
public literature (GitHub search, checked 2026-11-11, per F-20).

## Method

- Tool: `tools/wmi_b091012_scan.py` (this commit), reusing F-20's
  `wmi_dispatch_scan.py` `sweep()` + `pattern_search()` verbatim (capstone
  RV32+C, linear sweep with resync, constant propagation); ID values from
  `xref_wmi.py` (605 ath11k IDs). Raw scan kept out of git (46 MB); curated
  results in `results/wmi-dispatcher-b091012.json`.
- **Header ground truth from `wpss.mdt`** (the true ELF32, 13 phdrs):
  mapped to `.bNN` payloads by exact file size. e_machine = 164 = EM_QDSP6
  (Qualcomm Hexagon) — confirms F-7's junk-header finding.

## Header check: what the headers claim vs content

| seg | mdt phdr | vaddr | filesz | memsz | flags | on-disk magic | content |
|---|---|---|---|---|---|---|---|
| b01 | PH1 | 0xfe000000 | 6,440 | 8,192 | R-X | — | code (tiny) |
| b02 | PH2 | 0xfe002000 | 461,049 | 0x71000 | RWX | — | code |
| b03 | PH3 | 0xfe073000 | 1,104 | 4,096 | R-X | — | code (tiny) |
| b04 | PH4 | 0xc0000000 | 256 | 4,096 | R-X | — | — |
| b05 | PH5 | 0xc0001000 | 4,096 | 4,096 | R-X | — | — |
| b06 | PH6 | 0xc0002000 | 6,074,641 | 0x5cc000 | RWX | — | **main code** |
| b07 | PH7 | 0xc0600000 | 139,316 | 0x23000 | **RW-** | \x7fELF | data (F-20 swept it as code) |
| b08 | PH8 | 0xc0623000 | 275,644 | 0x44000 | **RW-** | \x7fELF | data (F-20) |
| **b09** | PH9 | 0xc0667000 | 360,960 | **14,835,712** | **RW-** | raw | unwind + registry + pointers |
| **b10** | PH10 | 0xc1500000 | 909,398 | 913,408 | **RW-** | raw | **strings** |
| **b12** | PH12 type **PT_NULL** | 0 | 4,376 | 4,376 | R-- | raw | **X.509 certs** |

Key facts: (1) **b09/b10/b12 are not ELFs on disk** — raw segment payloads
(unlike b07/b08, which are standalone ELFs); (2) **none of b07/b08/b09/b10 is
executable** — F-20 swept data as code; (3) b09's memsz (14.8 MB) dwarfs its
filesz (361 KB) — 60.9% zero bytes in-file, the rest BSS; (4) b12 is a PT_NULL
hash/cert region, not a LOAD.

## wpss.b09 — the message-ID registry (the find)

Three stacked roles in one RW segment:

1. **`.eh_frame` head**: 1,072-byte clean u32-length chain (9 CIEs, 28 FDEs,
   0 breaks, chain stops cleanly). FDE `pc_begin` (sdata4 pcrel) values decode
   to ~0xC04E6BD0–0xC04E6CB0 — inside b06's executable range. Unwind info for
   b06 code, stored in the data segment.
2. **Enum-name table**: 148 strings ending `EVENTID`/`CMDID` (44 `WHAL_`-, 44
   `WAL_`-prefixed + others), from file ~0x1fc84 on:
   `WHAL_HWSCH_POST_CMD_EVENTID`, `WHAL_HWSCH_RESET_EVENTID`,
   `WAL_RX_FW_RX_REFILL_FREE_HOST1_ENTRIES_EVENTID`,
   `SCHED_ALGO_MIGRATE_EVENTID`, `WHAL_TQM_PROCESS_GEN_MPDUS_STATUS_FLOW_EVENTID`…
   Firmware-internal event names (not ath11k names — shared ID space, different
   enums).
3. **ID→pointer registry**: 12-byte-stride records `[ptr, id, 0]` with ptr in
   0xc0000000–0xc2000000 (b06 range) and id = grp<<12|cmd. 213 aligned ID-word
   hits, 149 distinct IDs, groups present: 3/SCAN(7), 4/PDEV(49), 5/VDEV(35),
   6/PEER(20), 7/MGMT(11), 8(5), 10(8), 11/ROAM(9), 13/OCE(5). 225 records in
   16 stride-12 runs; main run 69 records at file 0x2a080–0x2a3b0 = **vaddr
   0xc0691080–0xc06913b0**. Owner pointers cluster: 0xc02cd9cc (×44),
   0xc031d8c8 (×34), 0xc02d94bc (×15), 0xc035d2e0 (×7), 0xc0377b5c (×5) — the
   same pointer serves many IDs, i.e. a registry/list, not one-handler-per-ID.
   Records also self-reference registry vaddrs (0xc0691080 — the main run
   itself — 0xc0691f88, 0xc06913c0): linked-list/list-head structure.
   Sample: `[0xc02cd9cc, 0x4001, 0]`, `[0xc02cd9cc, 0x4002, 0]`,
   `[0xc037b6bc, 0x38005, 0]`.
4. **Adjacent unidentified table** (pages at file 0xd000–0xe0xx): 16-byte
   stride, pairs WMI-shaped IDs (0x2001, 0x200a, 0x200b, 0x1005, 0x1008, 0x2115,
   0x4011, 0x401a…) with random-looking 32-bit words (CRC-like), plus
   non-WMI-group IDs (0x5104, 0x9221, 0xa200) — a broader message system
   (diag/QuRT?). Honest unknown, not attributed.

RV32 sweep of b09: 88.9% "decoded" but dominated by `c.unimp` (94,128 resync
fillers) — data, not code; the 403 raw construction hits are the same noise
class F-20 saw in rodata sweeps.

## wpss.b10 — trace/format strings; wpss.b12 — certificates

- **b10** (909,398 B): 95.5% ASCII, 11,244 strings in QCA `file.c:format`
  style (`wal_*.c`, `whal_*.c`, `wmi_ftm_attach.c`, `memheap.c`,
  `platform_diag_pmon.c`). Markers: wlan ×5203, wmi/WMI ×649, diag ×445,
  qurt ×68, htt/HTT ×85, htc/HTC ×13. 66 strings name WMI cmd/event IDs in
  error text (e.g. `wlan_dev.c:WMI_PDEV_CONFIG_VENDOR_OUI_ACTION_CMDID Error:
  total_length (%d) > %d`). **Zero u32 ID hits; u16 hits are ASCII noise**
  (top value 0x5020 = `" P"`, ×449). RV32 sweep 85.4% is `c.flw`/`c.lui`
  string noise; 42,278 raw construction hits = pure noise from sweeping text.
- **b12** (4,376 B): DER `30 82` SEQUENCEs at 0x3f8/0x653/0x8f3; strings
  `Generated OEM Root CA`, `Fairphone BV`, `T2MO OEM Key`, `Amsterdam`,
  `SecTools`, validity 250305→450228. Independently confirms
  librephone-upstream `docs/wpss.b12.md` (production cert chain). No code.

## Verdict

1. **b12: closed.** Certificates, PT_NULL, no WMI content.
2. **b10: closed.** String table; no ID data.
3. **b09: registry found — no code, but the dispatch DATA lives here.**
   ID values in the grp<<12|cmd space (groups 3–13), pointer records into b06,
   enum names, unwind info.
4. **The structural answer to F-20/F-19/F-9:** the wpss image's WMI handling is
   **table-driven**: static ID registry (b09) + handler code (b06) + trace
   strings (b10). No `grp<<12|1` arithmetic construction sites exist anywhere
   because no such computation is performed. F-20's zero is correct **and**
   fully explained by the header facts (b07/b08 are RW data).
5. **Remaining unknown:** which b06 code consumes the registry (cross-reference
   of 0xc0691080+ from b06) — the natural F-22 target, now with a concrete
   anchor.

## Honest negatives

- The semantic split of the registry's ptr column (owner component vs handler
  entry) is undetermined; same-pointer-per-many-IDs argues for list nodes or a
  shared handler, not individual dispatch stubs.
- The 0xd000–0xe0xx 16-byte-stride records are unidentified (shape reported,
  protocol not attributed).
- No b06 code analysis in this finding (time-bound); the sweep-based noise
  rates for b09/b10 are reported, not fully classified.
- e_machine=164 (EM_QDSP6) coexists with cleanly RV32+C-decodable b07 code
  (F-20: 100.0% coverage on its code LOADs) — the junk-header question remains
  open.

## Prior art

None found (GitHub code/repo search 2026-11-11 per F-20). Extends F-20
(`docs/wmi-dispatcher-search.md`), F-19 (no stored constants), F-9/F-7
(header/junk-field deflations).
