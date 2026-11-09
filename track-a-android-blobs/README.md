# Track A — Android Blob Reverse Engineering (for LibrePhone)

**Mission:** produce the first complete, public, clean-room documentation of
the proprietary blob families in a modern Android device, feeding the FSF's
[LibrePhone](https://www.fsf.org/news/librephone-project) initiative
(upstream: [codeberg.org/rsavoye/librephone](https://codeberg.org/rsavoye/librephone)).

## Why this is unique (verified gaps, Nov 2026)

- SRLabs (June 2025): *"no free tools or documentation exist"* for Qualcomm
  Hexagon firmware internals. Nothing since has closed this.
- Upstream LibrePhone is in analysis phase: 27 open issues, placeholder
  kernel module, wpss per-segment docs of only 7–40 lines each.
- Upstream's `docs/wireless.md` **guesses** the wpss image contains "an
  embedded 8-bit ATMel AVR core, and possibly a RISCV32 core" — unverified.
  Settling this from the ELF `e_machine` field is a concrete, publishable
  finding nobody has published.

## Target device & sources

- Device: **Fairphone FP6** (Qualcomm QCM6490, WCN6750 FastConnect 6700)
  — the same device upstream studies, so results merge upstream cleanly.
- Source: public LineageOS nightly
  `lineage-23.2-20261109-nightly-FP6-signed.zip` (no hardware needed).

## The full blob queue (directive #3: all of it)

| # | Family | Location in image | Upstream state | Our state |
|---|--------|-------------------|----------------|-----------|
| 1 | WiFi wpss (WCN6750) | `modem/image/qca6750/` | thin per-segment docs b01–b12 | 🟡 census first |
| 2 | Bluetooth (btnv/qca) | `bluetooth/` | none known | ⬜ |
| 3 | Modem (NON-HLOS, qdsp6) | `modem/image/` | tooling only (qdsp6-mdt-merge) | ⬜ |
| 4 | ADSP/CDSP/SDSP firmware | `dsp/` `firmware/` | none | ⬜ |
| 5 | TrustZone (tz, keymaster, gatekeeper) | `firmware/` | none | ⬜ |
| 6 | Fingerprint (goodix/fpc) | `vendor/firmware/` | none | ⬜ |
| 7 | Touchscreen controller firmware | `vendor/firmware/` | none | ⬜ |
| 8 | Sensors (sns, SLPI) | `vendor/firmware/` | none | ⬜ |
| 9 | DRM (widevine,_hdcp) | `vendor/firmware/` | none (policy-sensitive) | ⬜ docs-only census |
| 10 | eSIM/modem apps (mcfg, qmi configs) | `modem/mcfg/` | none | ⬜ |

## Method (reproducible, per family)

1. `census.py` — extract, hash, identify (file magic, ELF headers, MDT/PIL
   structure), classify per table above. Output: machine-readable JSON +
   markdown, no binary content.
2. Per-family deep dive: segment tables, string inventories, constant
   extraction cross-referenced against open driver sources (ath11k, kernel
   drivers), architecture identification, partial annotated disassembly.
3. Write family documentation in upstream's doc style; PR to Codeberg;
   mirror everything here with journal entries.

## First unique finding targets

1. wpss CPU architecture (settle AVR/RISCV32/other with evidence).
2. Complete segment map of all `wpss.bXX` files with load addresses & flags.
3. Cross-reference of firmware strings/constants to ath11k BMI/HTC/HTT/WMI
   message IDs — first public version-control-backed firmware↔driver map.
