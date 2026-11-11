# The WMI dispatch story at instruction level: the PDEV-family dispatcher's event-ID map and its registry tie-in (F-29)

*Investigator: F-29, 2026-11-12. Builds on F-28 (Hexagon decode unlocked,
track-a-android-blobs/docs/hexagon-decode.md) and F-22/F-23
(docs/wmi-dispatcher-b09-b10-b12.md, docs/wmi-registry-consumers.md). Inputs:
saved Ghidra 12.2 project (/tmp/f26/ghidra-proj, Hexagon:LE:32:default, base
0xc0002000), raw wpss.b06/wpss.b09, instruments/ath11k/wmi.h.*

## Claim

1. **The b06 function at `0xc02cd9cc` is a multi-group WMI event dispatcher
   whose complete event-ID → handler-block mapping is now decoded at
   instruction level: 61 events map to real handler blocks** — 41 PDEV (grp 4)
   via a b06-resident jump table, 9 STATS (grp 0x16) via a second jump table,
   6 MISC (grp 0x1d) and 2 GPIO (grp 0x1e) via cmp trees, 2 SUSPEND (grp 0x11)
   via cmp tree, 1 VDEV (grp 5, ID 0x5022) via a byte-compare. Unhandled IDs
   fall to a shared exit block `0xc02cedcc → jump 0xc04e61a8` (the stub
   cluster adjacent to the eh_frame region F-28 identified).
2. **The b09 registry is NOT the dispatcher's event jump table.** The
   event-level dispatch is done by computed jumps over **b06-resident tables**:
   PDEV table at `0xc056423c` (85 words, `memw R2,(R2<<#0x2+##0xc056423c);
   jumpr R2`, index = (ID&0xff)-1) and STATS table at `0xc05641fc` (16 words).
   No instruction operand anywhere in the 357,390 decoded packets of the saved
   program equals a registry record run start (0xc0691080 etc.) — the records
   are reached through pointer variables and head structures, not constants.
3. **The registry tie-in is nevertheless real, and now has a traced
   instruction-level chain (PARTIAL-YES):** the dispatcher materializes the
   **list-head structure that anchors the main registry run**
   (`assign R0,##0xc0691050` @0xc02cfb8c, `assign R0,##0xc0691068` @0xc02cfba0
   — the block containing b09[0xc0691078]=0xc0691080, F-23's run anchor) and
   writes `setbit()` masks into it (`memw (R0+#0xd8),setbit(#0x1)`,
   `+0x104`, `+0x118`, … → b09 0xc0691140/0xc069116c/0xc0691180, inside the
   record area) — i.e. the dispatcher **initializes/arms the registry head as
   an event-enable mask structure**. In the SUSPEND path it loads a
   runtime-initialized b09 pointer variable (`memw.if(P0)
   R2,(##0xc06bde64)` @0xc02cda20, then field `+0x1e8`). The registry's ptr
   column (all 69 records at this pointer) is the group→dispatcher routing
   level: registry record → 0xc02cd9cc → b06 jump table → per-event block.
4. **Cross-check between the two independent structures (new):** 40 of the 48
   registry PDEV records land on non-exit handler blocks; 8 registry IDs
   (0x4004, 0x4005, 0x4007, 0x4008, 0x4014, 0x4036, 0x403a, 0x404c) route to
   the shared exit in this dispatcher — candidates for handlers elsewhere or
   vestigial records; 1 handled ID (0x404e) has no registry record. STATS: 9 of 10
   registry records handled; 0x16003 routes to exit; no handled STATS ID
   lacks a record. The registry and the decode tree agree to ~85%
   (49 of 58 shared IDs non-exit: 40/48 PDEV, 9/10 STATS) — strong evidence both
   structures describe the same live dispatch system.
5. Per the prior-art audit (results/prior-art-audit.md) no published
   decode-level WMI dispatch analysis of this firmware exists; this ID→block
   map is first.

## Method

1. Full-function listing from the saved F-28 Ghidra project via PyGhidra
   (pattern from F-28's dump_listing.py): 0xc02cd9cc + 9,828 B = 0xc02cfd70;
   1,631 4-byte-aligned gaps explicitly disassembled → complete coverage,
   2,457 packets.
2. cmp/jump tree extraction from the listing (53 cmps, 48 explicit jumps
   parsed); register semantics pinned by the entry packet:
   `bitsplit R5R4,R1,#0x8` → R5 = ID>>8 (group select), R4 = ID&0xff; PDEV
   block computes index `add.if(P0.new) R2,R4,#-0x1`.
3. Jump-table words read from raw wpss.b06 at 0xc056423c (85×4 B) and
   0xc05641fc (16×4 B); every distinct target (53 addresses incl. exit and the
   0x5022 tail target 0xc02cb6dc) verified to hold a decoded Hexagon
   instruction in the saved project.
4. ath11k names assigned from `enum wmi_tlv_event_id` order (grp starts
   WMI_TLV_CMD(grp) = grp<<12|1): PDEV 0x4001–0x4022 named; 0x4023+ and parts
   of MISC beyond WMI_PKGID_EVENTID are firmware additions unnamed in ath11k.
5. Registry re-extraction from raw wpss.b09 with a looser group filter (grp
   ≤ 0x30): 69 records point at 0xc02cd9cc — 48 PDEV (matches F-22's 48
   exactly), 9 STATS, 7 MISC, 2 GPIO, 1 VDEV, 2 SUSPEND — cross-tabbed against
   the decoded tree.
6. Program-wide b09-reference scan over the saved project's instruction
   stream (357,390 instructions): operand scalars/addresses in b09 phdr
   0xc0667000–0xc06c4000 → 1,850 operand refs, 516 distinct addresses.

## The dispatcher at instruction level

```
c02cd9cc  bitsplit R5R4,R1,#0x8        ; R5=ID>>8, R4=ID&0xff
c02cd9e8  cmp.gt P0,R5,#0x15f          ; ID > 0x15fff ?
c02cd9ec  jump.if(P0) 0xc02cdaec       ; -> STATS/MISC/GPIO subtree
c02cd9f0  cmp.eq P0,R5,#0x40           ; PDEV?
c02cd9f4  add.if(P0.new) R2,R4,#-0x1   ; dispatch index = (ID&0xff)-1
c02cd9f8  jump.if(P0.new):nt 0xc02cdb8c
c02cd9fc  cmp.eq P0,R5,#0x50           ; VDEV?
c02cda00  jump.if(P0.new):nt 0xc02cdc80
c02cda04  cmp.eq P0,R5,#0x110          ; SUSPEND?
c02cda08  jump.if(!P0.new):nt 0xc02cedcc  ; else exit
...
c02cdb8c  cmp.gtu P0,R2,#0x54          ; PDEV: index<=0x54 else exit
c02cdb94  immext #0xc0564200
c02cdb98  memw R2,(R2<<#0x2+##0xc056423c)   ; LOAD b06 JUMP TABLE
c02cdbc4  jumpr R2                          ; per-event handler
...
c02cdaec  cmp.eq P0,R5,#0x160          ; STATS (grp 0x16)
c02cdaf8  cmp.eq P0,R5,#0x1d0          ; MISC   (grp 0x1d)
c02cdb00  cmp.eq P0,R5,#0x1e0          ; GPIO   (grp 0x1e)
...
c02cdc5c  cmp.gtu P0,R2,#0xf           ; STATS: index<=0xf
c02cdc64  memw R2,(R2<<#0x2+##0xc05641fc)   ; STATS JUMP TABLE
c02cdc68  jumpr R2
```

Note the F-22/F-23 group labels shift one slot: the 0x16xxx IDs are
**WMI_GRP_STATS (0x16)**, not PROFILE (0x10); 0x1dxxx is WMI_GRP_MISC
(0x1d), 0x1exxx WMI_GRP_GPIO (0x1e) — per `enum wmi_cmd_group` in
instruments/ath11k/wmi.h. The F-23 "PDEV(4)+MGMT/SUSPEND(17)" label was
PDEV + SUSPEND + STATS/MISC/GPIO records at the same pointer.

## ID → handler-block mapping (summary; full 101-entry map in results/wmi-pdev-dispatch-map.json)

Top-level selection: `R5 = ID>>8` → 0x40 PDEV, 0x50 VDEV, 0x110 SUSPEND,
0x160 STATS, 0x1d0 MISC, 0x1e0 GPIO; anything else → exit 0xc02cedcc.

PDEV jump table 0xc056423c (index = (ID&0xff)-1; **41 real, 44 exit**; IDs
0x4001–0x4055 covered; ath11k names 0x4001–0x4022). Handled subset (target =
b06 block):

| ID | ath11k name | block | | ID | ath11k name | block |
|---|---|---|---|---|---|---|
| 0x4001 | WMI_PDEV_TPC_CONFIG_EVENTID | 0xc02cdbc8 | | 0x401d | WMI_PDEV_CTL_FAILSAFE_CHECK_EVENTID | 0xc02ceae0 |
| 0x4002 | WMI_CHAN_INFO_EVENTID | 0xc02ce968 | | 0x401e | WMI_PDEV_CSC_SWITCH_COUNT_STATUS_EVENTID | 0xc02ce5f8 |
| 0x4003 | WMI_PHYERR_EVENTID | 0xc02cea10 | | 0x401f | WMI_PDEV_COLD_BOOT_CAL_DATA_EVENTID | 0xc02ce8f4 |
| 0x4006 | WMI_DFS_RADAR_EVENTID | 0xc02ce7c8 | | 0x4020 | WMI_PDEV_RAP_INFO_EVENTID | 0xc02cebb8 |
| 0x4009 | WMI_SERVICE_READY_EXT_EVENTID | 0xc02ce88c | | 0x4015 | WMI_PDEV_CHIP_POWER_SAVE_FAILURE_DETECTED_EVENTID | 0xc02ce654 |
| 0x400a | WMI_PDEV_FIPS_EVENTID | 0xc02ce71c | | 0x4016 | WMI_PDEV_CSA_SWITCH_COUNT_STATUS_EVENTID | 0xc02ce9f8 |
| 0x400b | WMI_PDEV_CHANNEL_HOPPING_EVENTID | 0xc02ce7b8 | | 0x4017 | WMI_PDEV_CHECK_CAL_VERSION_EVENTID | 0xc02ce8e8 |
| 0x400c | WMI_PDEV_ANI_CCK_LEVEL_EVENTID | 0xc02ceac8 | | 0x4018 | WMI_PDEV_DIV_RSSI_ANTID_EVENTID | 0xc02cea9c |
| 0x400d | WMI_PDEV_ANI_OFDM_LEVEL_EVENTID | 0xc02ce688 | | 0x4019 | WMI_PDEV_BSS_CHAN_INFO_EVENTID | 0xc02ceaa4 |
| 0x4010 | WMI_PDEV_SET_HW_MODE_RESP_EVENTID | 0xc02ce60c | | 0x401a | WMI_PDEV_UPDATE_CTLTABLE_EVENTID | 0xc02ceab0 |
| 0x404e | (fw-specific) | 0xc02ce590 | | 0x401b | WMI_PDEV_DMA_RING_CFG_RSP_EVENTID | 0xc02ceb14 |
| 0x4019–0x401a etc. (see JSON) | | | | 0x404d | (fw-specific) | 0xc02ce5e0 |

(Compact excerpt — the complete 85-row PDEV and 16-row STATS maps with
registry cross-check flags are in results/wmi-pdev-dispatch-map.json.
Every listed target was verified to decode as a Hexagon instruction.)

STATS table 0xc05641fc — 9 real: 0x16001 WMI_STATS_EXT_EVENTID→0xc02cdc6c,
0x16004 WMI_RADIO_LINK_STATS_EVENTID→0xc02ce0a0, 0x16005
WMI_UPDATE_FW_MEM_DUMP_EVENTID→0xc02ce058, 0x16006
WMI_DIAG_EVENT_LOG_SUPPORTED_EVENTID→0xc02ce198, 0x16008
WMI_RADIO_TX_POWER_LEVEL_STATS_EVENTID→0xc02ce1d4, 0x1600c
WMI_RADIO_CHAN_STATS_EVENTID→0xc02ce084, plus fw-specific
0x1600e→0xc02ce180, 0x1600f→0xc02ce18c, 0x16010→0xc02ce1e0.

MISC cmp tree (0xc02cdc94): 0x1d00b WMI_VDEV_GET_KEEPALIVE_EVENTID,
0x1d010 WMI_UPDATE_VDEV_RATE_STATS_EVENTID, 0x1d014
WMI_RSSI_BREACH_EVENTID, 0x1d019 WMI_PKGID_EVENTID + fw-specific
0x1d01a, 0x1d01d — 6 handled. GPIO tree (0xc02cdb08): 0x1e001
WMI_GPIO_INPUT_EVENTID, 0x1e002 WMI_UPLOADH_EVENTID. SUSPEND tree
(0xc02cda0c): 0x11001 WMI_PDEV_RESUME_EVENTID, 0x11002 (fw-specific).
VDEV: 0x5022 (fw-specific) → tail jump 0xc02cb6dc.

## Registry tie-in: the traced chain (2 loads + a write chain)

1. **SUSPEND path load (b09 pointer variable):** `memw.if(P0)
   R2,(##0xc06bde64)` @0xc02cda20 (P0 = R4==1, i.e. ID 0x11001
   WMI_PDEV_RESUME_EVENTID) → b09 0xc06bde64 (file-backed zero — a
   runtime-initialized pointer variable in the 0xc06bdb40-heavy b09 globals
   region) → `memw.if(P0) R17,(R2+##0x1e8)` @0xc02cda2c: field +0x1e8 of the
   runtime object. Chain: dispatcher → b09 pointer var → struct field.
2. **Registry-head materialization (the load-bearing one):** inside the same
   function, `immext #0xc0691040 / assign R0,##0xc0691050` @0xc02cfb88-8c
   followed by two `call 0xc0492640`; then `assign R0,##0xc0691068` +
   `assign R1,#0x142` @0xc02cfba0-a4, and a write sequence
   `memw (R0+#0xd8),setbit(#0x1)` / `+0x104` / `+0x118` / `+0x10`… → b09
   0xc0691140 / 0xc069116c / 0xc0691180 / 0xc0691078. b09 contents confirm
   the target: `b09[0xc0691060]=0xc06913c0` (pointer into the record area),
   `b09[0xc0691078]=0xc0691080` (F-23's main-run anchor), `b09[0xc0691074]=0x45`,
   `b09[0xc0691058]=0xffff`, `b09[0xc069105c]=0x1` — a list-head/enable-mask
   block immediately preceding the 225-record F-22 registry run 0xc0691080+.
   The dispatcher therefore **reads and writes the registry head structure by
   absolute address**, while the per-event routing stays in b06 tables.
3. **Why no instruction constant hits the record run starts:** the program-wide
   operand scan (357,390 instructions) found 1,850 b09 operand refs (516
   distinct addresses: 978 into 0xc06b0000+, 682 into the registry window
   0xc0682000–0xc06a0000, 140 below it, 50 at 0xc06c0000+) but **0 on the 28
   known run-start addresses** — record access is head-pointer + offset (the
   `+0xd8/+0x104/+0x118` pattern above) or via runtime pointer variables, not
   via materialized run-start constants. This resolves F-23's "the registry is
   reached via pointer variables (list-head anchors)" hypothesis at decode
   level: confirmed for the head; the record loop itself was not located (see
   negatives).

## What this settles

- F-28's open question "whether any reference targets the F-22 record registry
  0xc0691080+ specifically" — answered: the dispatcher targets the registry
  **head block** (0xc0691050/0xc0691068, containing the 0xc0691080 anchor and
  a pointer into the records at 0xc0691060), not run-start constants.
- F-28's `memw.if(P0) R2,(##0xc06bde64)` mystery — it is the SUSPEND
  (0x11001) handler's load of a runtime pointer, not a registry-record read.
- The dispatcher's "cmp/jump event tree" is exactly two levels: R5 (group)
  cmp tree → per-group table/tree → per-event block; 61 events resolved.
- Registry ↔ decode-tree agreement (40/48 shared PDEV IDs, 9/10 STATS non-exit) upgrade
  F-23's per-group mapping from structural to instruction-level.

## Honest negatives / limits

- The per-record consumption loop (walking [ptr,ID,0] records with stride 12)
  was **not located** — no decoded instruction materializes a run start
  (0xc0691080, 0xc0684da0, 0xc069dfc8, …); no 12-stride pointer-chase was
  identified inside the dispatcher. The registry→dispatcher call site (who
  calls 0xc02cd9cc with R1=ID) remains unknown; the dispatcher's own entry
  takes R1 and never dereferences the record ptr column.
- 8 registry PDEV IDs route to the shared exit (0x4004 PDEV_DUMP, 0x4005
  TX_PAUSE, 0x4007 L1SS_TRACK, 0x4008 TEMPERATURE, 0x4014 CHIP_POWER_STATS,
  0x4036, 0x403a, 0x404c — the last three fw-specific): either handled
  elsewhere, accepted-and-dropped, or vestigial records. Not resolved here.
- The 0x50 (VDEV) branch handles exactly one ID (0x5022, byte compare
  `cmpb.eq P0,R1,#0x22`); the main VDEV dispatcher 0xc031d8c8 (F-23's
  dominant) is untouched — separate function, same pattern expected.
- The saved program holds 357,390 decoded packets (~auto-analysis capped at
  300 s in F-28 + my gap fills); b06's full 6 MB contains more code — the
  program-wide b09 scan is over decoded instructions only, not all bytes.
  F-28's 33 raw-word window hits outside the decoded stream remain
  instruction-level unconfirmed (except 0xc057a518-30, which sit in b06 data,
  not code).
- Decompiler still unproven (not retried — CPU owned by T74); all analysis is
  disassembly-level.
- Handler-block *bodies* are mapped but not individually reverse-engineered;
  "handler" means decoded block reached for that ID.

## Data / repro

- results/wmi-pdev-dispatch-map.json — full 101-entry ID→block maps (PDEV 85,
  STATS 16), trees, tie-in chain, scan numbers, cross-tabs.
- Host (out of git): /tmp/f29/ (dump/parse/pass2 scripts, pdev-full-listing2.json,
  pass2-results.json, registry-runs.json), saved project /tmp/f26/ghidra-proj.
- Registry records at ptr 0xc02cd9cc: 69 (48 PDEV + 9 STATS + 7 MISC + 2 GPIO
  + 1 VDEV + 2 SUSPEND), re-derived from raw wpss.b09 (grp filter ≤ 0x30).
