# wpss firmware internals — RTOS identification & leaked source names

**Claim:** The WCN6750 wpss firmware (Moselle, `WLAN.MSL.3.0.1-00591`) runs
**Qualcomm's QURT RTOS on a RISC-V core**, and its build artifacts leak the
real source filenames used inside Qualcomm, including
`dog_hal_moselle_riscv.c`. No public source (ath11k docs, kernel patches,
SRLabs, LWN, XDA, GitHub code search — checked 2026-11-09) documents the
wpss's RTOS or these internals.

## Evidence (strings from `wpss.b07` / `wpss.b08`, full lists in this dir)

### RTOS: Qualcomm QURT

```
%x%x Thread start utcb=0x%X
%x%x Thread stop utcb=0x%X
%x%x control reached after QURTK_thread_stop. TCB: 0x%x
%x%x main task reached end
%x%x Int%d enable failed
%x%x error in setup root thread
Could not register qurt fatal notification handler
EXCEPTION:tid=0x%x:PC=0x%x:mcause:0x%x
```

- `QURTK_*` and UTCB/TCB vocabulary is Qualcomm's proprietary RTOS (same
  API family as the Hexagon DSPs' QuRT). First public identification of
  QURT on the wpss.
- `mcause` is a RISC-V CSR name — the exception path is RISC-V, again
  confirming the architecture census (F-5) at the RTOS layer.

### Leaked source filenames (Qualcomm build artifacts)

```
dog_hal_moselle_riscv.c     ← watchdog HAL: "moselle" + "riscv" in the filename
err_inject.c                ← error-injection subsystem (test hooks in production firmware)
err_sol.c / err_sol         ← "SOL" (signal-of-life) GPIO subsystem
```

- `dog_hal_moselle_riscv.c` is Qualcomm's own naming: the Moselle (WCN6750)
  watchdog HAL targets RISC-V — a third independent confirmation.
- Watchdog behaviour strings: `Dog Bark ISR fired %d`,
  `Dog defer_kick_timer def failed`, `Dog failed to register with interrupt
  controller`.
- SOL: `SOL GPIO ISR triggered`, `SOL GPIO status read failure` — the
  signal-of-life heartbeat path (relevant for anyone debugging dead-wpss
  devices on free stacks).

### Transport evidence (aligns with upstream's IPCI/ICNSS2 doc fix)

```
Endpoint assert WAKE#          (wpss.b07)
Endpoint deassert WAKE         (wpss.b07)
ERR_ZERO_IPC_BUFFER            (wpss.b08)
ERR_append_ipc_buf_in_flight   (wpss.b08)
SYS:IPC loc-1 / SYS:IPC loc-2  (wpss.b08)
```

- PCIe-style endpoint WAKE signalling + dedicated IPC buffer error codes:
  the host↔wpss path is an IPC transport with wake handshake — matches
  upstream's corrected "WCN6750 transport to IPCI/ICNSS2" description.

## Method

`strings -n 6` on the extracted segments (see repo tools + census doc for
extraction provenance). Full raw string lists committed here as derived
facts (strings are facts about the binary, not redistributable binary
content).

## Next

- Map QURT thread/IPC calls against the disassembly (tools/wpss_disasm.py).
- Cross-reference WAKE#/IPC constants with ath11k's `htc.c`/`htc.h`
  and the kernel's iccnss/ipci drivers.
- Look for the BMI/HTC boot handshake constants inside wpss.b07 code
  (immediate operands matching `ath11k` message IDs).

## First XREF attempt — documented negative result (2026-11-09)

Two passes to find ath11k's HTC service/message IDs inside the firmware:

1. Raw LE16/LE32 byte scan of wpss.b07/b08 (tools/xref_constants.py): hits
   everywhere — useless, small values collide with ordinary data.
2. Immediate-operand scan of decoded RV32+RVC instructions
   (tools/xref_immediates.py; 1,355 instructions decoded from the b07 entry
   segment): HTC IDs 1–4 appear only as colliding small immediates
   (`c.lui t0,2`, `c.andi a0,4`…). No meaningful match.

Interpretation: the boot protocol constants are not naked immediates in the
decoded region — they are either in literal pools (capstone stopped at the
segment boundary; the driver-facing logic likely lives in wpss.b08's
262 KB ucode segment), constructed arithmetically, or the firmware uses a
different HTC dialect. **Queued:** literal-pool sweep of wpss.b08, and
cross-referencing the IPC/WAKE strings against the kernel's iccnss/ipci
drivers instead of ath11k's HTC layer.
