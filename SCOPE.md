# SCOPE — Directives from the lab owner

Standing instructions, recorded verbatim-in-substance so the lab never drifts.

1. **Uniqueness bar.** "Everything produced here must be unique — no one may
   have done it before. Never build anything that has already been built.
   Research it beforehand: search the whole internet FIRST." — every
   deliverable must target a verified gap. Prior-art checks are mandatory
   before writing up anything as a finding.
2. **Discovery / RE / research.** "Discover something or reverse engineer
   something or research in someplace." Original findings only.
3. **LibrePhone — all of it.** "There are many things in librephone to
   reverse engineer, do all that." Track A is not just the WCN6750 wpss —
   the full blob census of the FP6 image: WiFi (wpss), Bluetooth, modem
   (NON-HLOS / qdsp6), DSPs (adsp/cdsp/sdsp), TrustZone, fingerprint,
   touchscreen, sensors, DRM. Systematic, per-family documentation.
4. **Cross-vendor expansion.** "Reverse engineer everything like MediaTek
   proprietary blobs etc." — the MediaTek front is active (MT6785 rosemary
   census complete); expand to other MTK generations and other vendors.
5. **MediaTek open-source path.** "Will you make open-source versions of
   MediaTek proprietary drivers, source code, kernel source, and closed-
   source vendor blobs?" — the lab's role is the clean-room SPEC producer:
   ISA maps, protocol specs, format layouts that make open-source
   implementation possible without touching proprietary code. The lab does
   NOT write the firmware itself — it produces the specs. (2026-11-13)
6. **Internet-wide scouting.** "Search the whole internet to find something
   worth contributing to research or other fields" — continuously search
   for fields that need contribution or research, beyond LibrePhone.
7. **Famous projects as instruments.** "Download projects famous in github
   like rea or research agent or something to find unique things with the
   help of that" — use famous GitHub projects as discovery instruments,
   never rebuild them.
8. **Improve previous work.** "If you found something that can be improved
   based on the previous work do it that also" — Rule 1 in AGENTS.md.
9. **Papers.** Findings mature into research-paper-grade writeups under
   papers/.
10. **Note everything.** All directives, decisions, findings — including
    negative results — are recorded in this repo and the journal.
11. **Fleet.** Two agents concurrent, file-wall isolation, F-numbers at
    merge, silent-death detection, resume via SendMessage.
12. **Repo structure.** Separate repos: librephone-blob-research (Android
    blob RE) and open-research-lab (math + astronomy + discovery engine);
    open-discovery-lab is the umbrella lab notebook.
13. **Exclusions.** CVE hunting (excluded 2026-11-09). Classical-cipher
    cryptanalysis (excluded 2026-11-09). May be revisited only at owner's
    request.
14. **Adversarial audit.** A dedicated prior-art audit agent re-attacks
    every claim every ~10 findings or per session. A finding survives only
    if the auditor genuinely tried to break it.
