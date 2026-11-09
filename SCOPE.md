# SCOPE — Directives from the lab owner

Standing instructions, recorded verbatim-in-substance so the lab never drifts.

1. **Uniqueness bar.** "I just don't want to make something that people have
   already built" — every deliverable must target a verified gap. Prior-art
   checks are mandatory before writing up anything as a finding.
2. **Discovery / RE / research.** "Discover something or reverse engineer
   something or research in someplace." Original findings only.
3. **LibrePhone — all of it.** "There are many things in librephone to
   reverse engineer, do all that." Track A is not just the WCN6750 wpss —
   the full blob census of the FP6 image: WiFi (wpss), Bluetooth, modem
   (NON-HLOS / qdsp6), DSPs (adsp/cdsp/sdsp), TrustZone, fingerprint,
   touchscreen, sensors, DRM. Systematic, per-family documentation.
4. **Internet-wide scouting.** Continuously search for fields that need
   contribution or research, beyond LibrePhone (astronomy mining already
   adopted; the search continues in Track C).
5. **Famous projects as instruments.** Clone and mine well-known GitHub
   projects (awesome-rea, RE tooling, research-agent projects) to find unique
   things — use them, don't rebuild them.
6. **Papers.** Findings mature into research-paper-grade writeups under
   `papers/`.
7. **Note everything.** All directives, decisions, findings — including
   negative results — are recorded in this repo and the journal.
8. **Excluded by owner decision (2026-11-09):** CVE hunting as a primary
   track; classical-cipher cryptanalysis (e.g., D'Agapeyeff). May be revisited
   only at owner's request.
