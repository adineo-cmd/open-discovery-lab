# EVROS chip identity — it is Qualcomm WCN6450

**Claim:** The FP6's third BT/WLAN firmware family ("EVROS": `evrbtfw20.tlv`,
`evrnv20.bin`, TLV `product_id` 29, `BTFW.EVROS.2.0.0-00143-PATCHZ-5_DEF`,
`WLAN.EVR.1.0-…-QCAEVRSWPLZ-1` — F-14, [[bt-firmware-census]]) belongs to
**Qualcomm WCN6450**, the low-tier WLAN+BT combo companion (Wi-Fi 6, 1×1,
BT 6.0 per leaked platform datasheets). **Confidence: high** — six
independent public Qualcomm code trees agree, and every number in the
chain reproduces against the FP6 binaries (product_id 29 = 0x1D,
rom_build 0x0200 = EVROS soc-id low word). On the FP6 (QCM6490), WCN6750
"Moselle" is the active primary; EVROS firmware is shared-Lanai-BSP
support for the WCN6450 board variant, and upstream Linux has **zero**
`wcn6450` mentions — the "Linux cannot name it" observation (F-14) stands.

**Prior art checked (2026-11-12):** F-14's census (2026-11-10) had flagged
"which SoC is EVROS?" as open. GitHub code search `evrbtfw20` (3 hits),
`QCAEVRSWPLZ` (2 hits: ver_info.txt device dumps), and `"wcn6450"
repo:torvalds/linux` (**0 hits**) — no public source previously tied the
`evr*` firmware family to a named part; nothing to attribute. This doc is
the identification, not a correction.

## Evidence chain (all fetched 2026-11-12, refs = commit SHAs)

1. **Qualcomm's own WLAN framework (qsdk) names the pair.**
   `qca/src/qca-wifi/cmn_dev/hif/inc/target_type.h`
   ([everything411/qsdk @ 30f8398f](https://github.com/everything411/qsdk/blob/30f8398fa2da1decd57e12f771010c5a215ecab2/qca/src/qca-wifi/cmn_dev/hif/inc/target_type.h)):
   ```c
   /* Evros */
   #ifndef TARGET_TYPE_WCN6450
   #define TARGET_TYPE_WCN6450 38
   #endif
   ```
   and `hif_main.h` (same tree):
   ```c
   /*TODO: change IDs for Evros */
   #define WCN6450_DEVICE_ID (0x1108)
   ```
   plus `target_if_cfr.c`: `TARGET_TYPE_WCN6450 → CFR_CAPTURE_RADIO_EVROS`,
   a dedicated `hal/wifi3.0/wcn6450/` HAL dir and `hif/src/wcn6450def.h`.
   A comment and a #define on adjacent lines — the codename→part mapping
   is explicit in Qualcomm's own source.

2. **The Qualcomm BT vendor HAL maps the DT compatible to the codename.**
   `ftm/ftm_main.c`
   ([aospa-op13/proprietary @ 165e8273](https://github.com/aospa-op13/proprietary/blob/165e827303fd78898ad287e867c49561e84ed97c/ftm/ftm_main.c)):
   ```c
   else if (strstr(compatable_chipset_id, "wcn6450")) {
       ret = property_set("persist.vendor.qcom.bluetooth.soc", "evros");
   ```

3. **The same HAL's patch table contains the FP6's exact filenames, keyed
   by an EVROS product id that equals the FP6 TLV product_id.**
   `bluetooth/hidl_transport/bt/1.0/default/patch_dl_manager.h` (same tree,
   SHA 7f9ca219):
   ```c
   enum {
     ...
     PROD_ID_MOSELLE      = 0x15,
     ...
     PROD_ID_BT_SOC_EVROS = 0x1D,
   };
   enum { QCA_EVROS_BT_SOC_ID_0100 = 0x40200100, QCA_EVROS_BT_SOC_ID_0102
          = 0x40200102, QCA_EVROS_BT_SOC_ID_0104 = 0x40200104, };
   enum { QCA_EVROS_BT_SOC_ID_0200 = 0x40200200 };
   enum { EVROS_BT_VER_2_0 = QCA_BT_VER(QCA_EVROS_BT_SOC_ID_0200,
          PROD_ID_BT_SOC_EVROS, EVROS_BT_BUILD_VER_0200), };
   ```
   and `patch_dl_manager.cpp` (same tree): `EVROS_BT_VER_2_0 →
   PatchPathManager("EVROS_BT2_0", "evrbtfw20.tlv", "evrnv20.bin")`
   (with `EVROS_BT_VER_1_0/1_2 → evrbtfw10.tlv/evrnv10.bin` — an earlier
   EVROS BT generation that also exists). **Numeric locks against the FP6
   binaries** ([[bt-firmware-census]]): TLV `product_id` 29 = 0x1D =
   `PROD_ID_BT_SOC_EVROS` (and Moselle's product_id 21 = 0x15 =
   `PROD_ID_MOSELLE` — the HAL enum IS the TLV field's namespace);
   `rom_build` 0x0200 = the EVROS 2.0 soc-id/build low word (`…0200`).
   The kernel's own `rom_ver` math (0x0200 → 32 → "evrbtfw20", F-14)
   completes the filename loop.

4. **BT kernel drivers carry the same EVROS soc IDs.**
   `soundwire/btfm_swr_slave.h`
   ([sonyxperiadev/vendor-qcom-opensource-bt-kernel @ ad503d91](https://github.com/sonyxperiadev/vendor-qcom-opensource-bt-kernel/blob/ad503d914dcdcae41b2a46aad8804b58d1539cdc/soundwire/btfm_swr_slave.h),
   [mvaisakh/xiaomi14 @ a3d23d9f](https://github.com/mvaisakh/xiaomi14/blob/a3d23d9fb2f76b6b6407e51081ba348898669d20/techpack/bt/soundwire/btfm_swr_slave.h)):
   `QCA_EVROS_SOC_ID_0100 = 0x40200100, QCA_EVROS_SOC_ID_0104 =
   0x40200104, QCA_EVROS_SOC_ID_0200 = 0x40200200` → enum `EVROS` in
   `btfm_swr.c`. Values identical to the HAL's — two independent trees.

5. **Device trees ship WCN6450 boards literally named Evros.**
   `wlan-devicetree/volcano-wcn6450.dtsi`
   ([aospa-op13/proprietary @ 165e8273](https://github.com/aospa-op13/proprietary/blob/165e827303fd78898ad287e867c49561e84ed97c/wlan-devicetree/volcano-wcn6450.dtsi)):
   `icnss2: qcom,wcn6450 { compatible = "qcom,wcn6450"; }` and
   `wpss_pas: remoteproc-wpss@9bb00000 { firmware-name = "wcn6450/wpss.mdt"; }`;
   `bt-devicetree/volcano-wcn6450-bt.dtsi`: `compatible = "qcom,wcn6450-bt"`.
   Board model strings: `"Qualcomm Technologies, Inc. Volcano IDP +
   Evros"`, `"Volcano MTP + … + Evros"`
   ([lanai-kernel-devicetree/kernel-audio-devicetree @ 879bb69c](https://github.com/lanai-kernel-devicetree/kernel-audio-devicetree/blob/879bb69ca628153e2028bc0318effa945295f3b7/volcano-audio-cdp-wcn6450.dts)),
   and `"Chora QRD evros"` / `chora-*-wcn6450.dts`
   ([rk134/kernel_oneplus_sm8750-devicetrees @ 838236ec](https://github.com/rk134/kernel_oneplus_sm8750-devicetrees/blob/838236ece3273357daf6110eab70d32e7fc95fb7/qcom/wlan/chora-qrd-wcn6450.dts)).

6. **The ICNSS2 platform probe maps the PCI-style device id to the
   codename.** Decompiled `icnss2/icnss_probe.c`
   ([Coding-BR/android_kernel_nubia_sm8850_qwjujube @ efee6f41](https://github.com/Coding-BR/android_kernel_nubia_sm8850_qwjujube/blob/efee6f411184886b0fbdaf63fc9db36b3ed96036/decompiled/icnss2/icnss_probe.c)):
   `if (v4 == 25680) { v5 = "EVROS"; }` — 25680 = 0x6450, i.e. WCN**6450**.

7. **The part is official even without a datasheet.** WCN6450 appears in
   Qualcomm security bulletins (docs.qualcomm.com, e.g. CVE-2024-49848,
   CVE-2025-21479 affected-chip lists) and NVD carries CPE
   `qualcomm:wcn6450_firmware`.

8. **Public positioning matches the FP6 usage pattern.** Leaked
   Snapdragon 4 Gen 6 datasheet coverage (GSMArena / NotebookCheck et al.,
   July 2026) lists **WCN6450 = Wi-Fi 6, 1×1, Bluetooth 6.0** — the
   low-tier companion option next to WCN6750 (Wi-Fi 6, 2×2). Same BOM
   family, two tiers — which is exactly why the shared Lanai-family
   metabuilds ship **both** firmware families: `ver_info.txt` lists
   `wlan_evr: WLAN.EVR.1.0-01270-QCAEVRSWPLZ-1` AND `wlan_msl:
   WLAN.MSL…` side by side in the Redmi `flute`/`malachite` dumps
   ([ChkDumps/redmi_flute_dump @ 0a3028e3](https://github.com/ChkDumps/redmi_flute_dump/blob/0a3028e3693849ae83c586723acfc7f1df83eac2/modem/verinfo/ver_info.txt),
   [redmi_malachite_dump @ 879c5cd7](https://github.com/ChkDumps/redmi_malachite_dump/blob/879c5cd727b6a01b2bf9ba488a6fdacdd5d1d529/modem/verinfo/ver_info.txt)) —
   the same LANAI TZ metabuild as the FP6.

## What this means for the FP6

- The FP6's active WLAN/BT is **Moselle (WCN6750)** (`wpss.b07` =
  `WLAN.MSL…`, F-5/F-14; ath11k WCN6750). EVROS/WCN6450 firmware in the
  `bluetooth` partition is best read as **shared-BSP support for the
  WCN6450 board variant of the same Lanai-family platform** — selected
  only when the device tree carries `qcom,wcn6450-bt` (the BT HAL's
  `compatable_chipset_id` probe), i.e. a BOM/SKU alternative, not a
  second active controller. Which chips a given FP6 unit actually
  enumerates remains runtime-observable only (F-14 caveat stands, now
  with the correct name on it).
- **Upstream Linux status unchanged but now precise:** 0 hits for
  `"wcn6450" repo:torvalds/linux` (GitHub code search, 2026-11-12); no
  `evr` string in `btqca.c/hci_qca.c`; no ath11k/ath12k WCN6450 support
  surfaced. WCN6450 would enter mainline (if ever) through the
  ath11k/ath12k + cnss2 route — its firmware family would land in
  linux-firmware `qca/` as `evr*`/`wcn6450/*`, neither of which exists
  today (F-14's linux-firmware audit).

## Discrepancy noted

An anonymous engineer resume (Scribd, surfaced 2026-11-12) describes
"Project Evros" as a "1×1, 80 MHz Wi-Fi **7** station chipset for
low-tier mobile chipsets". The Wi-Fi 7 claim conflicts with the Wi-Fi 6
1×1 leaked-datasheet row and with WCN6450's integration in the
Wi-Fi 6-class `qca-wifi` `wifi3.0` HAL tree; everything else in the
resume ("1×1", "low-tier mobile chipsets") matches. Treated as weak
secondary evidence; does not affect the identification.

## Negatives

- No public WCN6450 datasheet or product page (NDA-only; NVD/bulletin
  lists only).
- `evrbtfw10.tlv`/`evrnv10.bin` (EVROS BT 1.0/1.2/1.4 generation) are
  named in the HAL but not shipped on the FP6 — the FP6 carries only the
  EVROS 2.0 generation.
- The 0x1108 `WCN6450_DEVICE_ID` (qsdk HIF) vs 0x6450 (icnss2) are two
  different id namespaces (HIF CE device id vs platform probe id); both
  carry the "6450" number and both map to Evros.

## Reproduce

```
# GitHub code search (2026-11-12):
QCAEVRSWPLZ                    -> 2 hits  (ChkDumps ver_info dumps)
evrbtfw20                      -> 3 hits  (HAL dumps, files.md)
EVROS_BT_VER                   -> 6 hits  (patch_dl_manager.{h,cpp}, data_handler.cpp)
"evros" language:c             -> qsdk target_type.h / hif_main.h / CFR, btfm drivers
wcn6450                        -> 3600 hits (qsdk, qcacld configs, devicetrees)
"wcn6450" repo:torvalds/linux  -> 0 hits
```
Headers verified by direct fetch: `patch_dl_manager.h`
(aospa-op13/proprietary @ 165e8273, SHA 7f9ca219) —
`PROD_ID_BT_SOC_EVROS = 0x1D`, `QCA_EVROS_BT_SOC_ID_0200 = 0x40200200`.
