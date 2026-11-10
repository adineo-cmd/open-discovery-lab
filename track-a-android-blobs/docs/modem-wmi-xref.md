# WMI constant cross-reference: ath11k ↔ FP6 modem (mpss) Hexagon segments

**Claim:** NO — the Fairphone FP6 modem firmware (mpss, Hexagon/e_machine 164)
does not store ath11k WMI command/event IDs in any way that distinguishes it
from an unrelated Qualcomm DSP. Every value family that survives the aligned
LE32 scan in the modem — including the WLAN-profile family (0x10001–0x10005)
that F-9 flagged in the wpss — also appears in a **negative control**
(adsp.b36, audio/sensors DSP) at comparable or higher multiplicity, with the
same adjacency structure. The modem therefore contributes no evidence for a
modem-side WMI endpoint, and the value-presence criterion is now shown to be
too weak to attribute WMI-ness anywhere in these firmwares. The F-9
structural conclusion (wpss is the WMI endpoint; dispatcher computes IDs at
runtime) stands, and static constant xref is now exhausted across wpss,
modem, and control.

## Method

1. Segment selection: 10 largest `modem.*` segments in
   `trees/modem/image/` (mpss ELF PT_LOAD slices; e_machine 164 = Hexagon),
   covering ~110 MB of the ~120 MB mpss payload:
   b23 (39.6 MB), b24 (28.9 MB), b18 (12.5 MB), b19 (12.4 MB), b20 (4.9 MB),
   b13 (4.6 MB), b11 (4.0 MB), b15 (3.9 MB), b08 (2.5 MB), b25 (1.3 MB).
2. `tools/xref_wmi.py` (the verified evaluator from F-9) over all 10, with
   **adsp.b36 (6.4 MB) as a negative control** — a Qualcomm DSP firmware that
   should carry no ath11k WMI surface.
3. Targeted re-scan (count + offset extraction) for the discriminating
   families the top-40 printout exposed: WLAN-profile grp 0x10
   (0x10001–0x10005), TDLS grp 0x20 (0x20001/0x20002), grp 0x30
   (0x30001/0x30002), grp 0x40 spatial-reuse (0x40001/0x40002).
4. F-9's cluster test, generalized: largest 2 KB window containing distinct
   profile values, run on modem segments, the control, and wpss.b08 for
   reference.
5. Strings pass (`strings -n 8|10` + marker grep) on modem.b19 (highest
   discriminating-family density) and modem.b23 (highest matched-ID count).

Note on encodings: `WMI_TLV_CMD(grp) = (grp<<12)|1`; CMDID/EVENTID pairs
share values by construction (each distinct value counts two ath11k names),
and the tool's per-segment printout is capped at 40 lines while the matched
count itself is complete.

## Results

### xref_wmi matched-ID counts (605 IDs, aligned LE32)

| segment | size | matched IDs | top-40 family mix | adj-pairs |
|---|---|---|---|---|
| modem.b23 | 39.6 MB | 366 | PDEV 22, ROAM 5, TDLS 4, PROFILE 3, 0x40-grp 2 | 13 |
| modem.b24 | 28.9 MB | 177 | PDEV 22, PROFILE 5, 0x30 4, TDLS 3 | 12 |
| modem.b18 | 12.5 MB | 44 | PDEV 10, PEER 4, 0x30 3 (18 groups) | 14 |
| modem.b19 | 12.4 MB | 118 | PDEV 14, PROFILE 5, TDLS 4, 0x30 4 | 16 |
| modem.b20 | 4.9 MB | 216 | PEER 12, PDEV 8, TDLS 4, PCA 4 | 13 |
| modem.b13 | 4.6 MB | 123 | PDEV 38 | 18 |
| modem.b11 | 4.0 MB | 122 | PDEV 40 | 18 |
| modem.b15 | 3.9 MB | 0 | — | — |
| modem.b08 | 2.5 MB | 119 | PDEV 40 | 19 |
| modem.b25 | 1.3 MB | 0 | — | — |
| **adsp.b36 (control)** | 6.4 MB | 140 | PDEV 39, PROFILE 1 | 19 |

### Targeted family counts (aligned LE32, modem vs control)

| value | family | b19 | b20 | b13 | b23 | b24 | b18 | **adsp.b36 ctrl** |
|---|---|---|---|---|---|---|---|---|
| 0x10001–05 | PROFILE (5/5) | 4236/1091/550/822/605 | 179/23/5/14/4 | 329/16/5/5/2 | 28/11/11/4/0 | 27/12/4/4/5 | 6/5/0/0/0 | **513/38/31/12/17** |
| 0x20001/02 | TDLS | 497/1823 | 142/28 | 2/19 | 71/8 | 16/12 | 0/0 | **166/303** |
| 0x30001/02 | grp 0x30 | 192/261 | 120/21 | 1/36 | 3/7 | 10/6 | 6/1 | **80/68** |
| 0x40001/02 | grp 0x40 | 125/103 | 124/7 | 4/0 | 11/36 | 4/7 | 6/4 | **42/39** |

### 2 KB window cluster test (distinct profile values in best window)

| segment | 0x10001..05 counts | 5/5 in 2 KB? |
|---|---|---|
| modem.b19 | 4236/1091/550/822/605 | 5/5 (trivial) |
| modem.b20 | 179/23/5/14/4 | 5/5 (trivial) |
| modem.b13 | 329/16/5/5/2 | 5/5 (trivial) |
| **adsp.b36 control** | 513/38/31/12/17 | **5/5 (trivial)** |
| wpss.b08 (F-9 reference) | 1/2/4/5/4 | 4/5 |

### Strings characterization

- **modem.b19** (52,365 strings): the cellular protocol/data stack —
  `ds_3gpp_*`, `ds_iwlan_s2b_*` (VoWiFi ePDG handlers — "iwlan" here is
  cellular IWLAN, not ath11k WLAN), QMI framework (`QMI_MPROC_SVC_PRI_ORDER`,
  QMI send/receive error strings), RF L1 (`srch_idle_pingpong`). Marker
  counts: wmi 1 (a filename `ds_3gpp_l2wmif_mgr.c`), QMI 528, wlan 66
  (all `ds_iwlan_*`/`ciwlan`), **HTC 0, HTT 0, ath11k 0, WCN 0**.
- **modem.b23/b24** (68 MB combined): opaque — compressed/packed payloads,
  no extractable protocol strings.

## Cluster assessment (F-9 standard + control)

1. **PDEV range 0x4001–0x4050 = structured, non-specific noise.** It is the
   dominant "hit" in every scanned segment *including the control* (39/40 of
   adsp.b36's shown hits; all-40 in modem.b11/b08/b13). Multiplicities run to
   918+ for single values — too dense to be random, but identical structure
   in an unrelated DSP means the family is a generic Qualcomm firmware
   constant pattern (plausibly protocol/message-ID tables), *not* ath11k WMI
   PDEV commands. Presence in the control kills the attribution.
2. **WLAN-profile family (0x10001–0x10005) is not WMI-specific.** All five
   values appear in the control (12–513× each) with the same adjacency
   behavior as in the modem. The 2 KB cluster criterion that F-9 used as
   family evidence passes trivially at these counts (any dense QC firmware
   reaches 5/5). This retroactively weakens F-9's profile-family cluster as
   *positive* WMI evidence for the wpss: value-presence alone cannot carry
   the WMI claim. (wpss.b08's counts — 1–5 per value — remain low and
   unusual, but the cluster criterion does not discriminate.)
   *Reproduction note:* F-9's table implies 5/5-in-2 KB, but its own first@
   offsets span >2 KB for 0x10001; a strict 2048-byte sliding window on
   wpss.b08 yields **4/5**. The structural observation (low counts, (cmd,
   status)-pair region) survives; the window phrasing should read 4/5.
3. **TDLS / grp-0x30 / grp-0x40: same verdict** — present in modem and
   control alike.
4. **No modem-exclusive WMI signature exists.** Nothing in the modem scan
   distinguishes it from the adsp control; two segments (b15, b25) have zero
   matches; the two largest are opaque packed payloads.

## Implications for the WMI-endpoint question

- The modem (mpss) holds **no** ath11k WMI constants that the wpss lacks —
  and nothing WMI-specific at all once the control is applied.
- modem.b19's content (3GPP/IWLAN-S2B/QMI/RF) confirms the modem is the
  cellular processor; it carries no HTC/HTT/ath11k transport markers.
- Combined with F-9 (605 IDs absent as stored constants in wpss.b07/b08;
  core SCAN/PDEV/VDEV families nowhere), the endpoint question is now settled
  **structurally**: static WMI-constant xref has been run across wpss, modem,
  and a DSP control, and no firmware on this device stores a WMI dispatch
  table as aligned constants. The wpss remains the WMI endpoint (it is the
  WCN6750 target), with IDs computed at runtime (`grp<<12|1` construction);
  next leverage, if any, is the dispatcher's immediate-operand sites, not
  more segment scans.

## Honest negatives / tooling limits

- xref_wmi.py prints at most 40 hits per segment (matched count is complete);
  discriminating families were re-scanned by a targeted script instead.
- CMDID/EVENTID value sharing means "matched IDs" double-counts names per
  value; distinct-value counts are the real signal.
- The PDEV-range "noise" is itself structured (high multiplicity, adjacency)
  — an alignment-only scan cannot reject it; only the control comparison did.
- b23/b24 (68 MB) are packed/compressed: their contents are unverified; if a
  WMI table hides in a compressed payload, this scan cannot see it (same
  limitation applied to F-9's wpss scan).
- No e_machine/triple check was needed for the negative segments beyond
  family size (census.py's corrected registry is orthogonal here).

## Tool provenance

- `tools/xref_wmi.py` — reused as-is from F-9 (verified evaluator).
- Analysis scripts were one-off (`/tmp`): targeted value scanner, 2 KB window
  test, output parser — logic fully reproduced in the tables above;
  raw per-segment hit table in `results/modem-wmi-xref.json`.
- Inputs: `instruments/ath11k/wmi.h` (605 IDs = 398 CMDID + 207 EVENTID);
  `trees/modem/image/` from the LineageOS FP6 modem package.
