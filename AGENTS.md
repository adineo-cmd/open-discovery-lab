# AGENTS.md — standing rules for every agent working in this repo

## ⚠️ RULE 0 — PARAMOUNT: ABSOLUTE UNIQUENESS (owner directive, never override)

**Everything produced here must be unique — no one may have done it before.
Never build anything that has already been built. Research it beforehand:
search the whole internet FIRST.**

Mandatory sequence for every task and finding:

1. **Search before building** — GitHub code search (excluding
   adineo-cmd/*), the wider web (XDA, Reddit, LWN, HN), arXiv/Scholar,
   OEIS (math), linux-firmware/kernel trees (firmware coverage). Record
   exact query strings and dates in the deliverable.
2. **Prior art found → do not rebuild.** Find the genuinely new delta or
   pick a different target. Partial overlap is still overlap.
3. **Adversarial audit after** — a dedicated prior-art audit agent
   re-attacks every claim (run every ~10 findings or per session). A
   finding survives only if the auditor genuinely tried to break it.
4. **Corrections in place** — any finding that fails the audit is
   corrected where the original claim lives (precedent: F-9 corrected by
   F-19's negative control, banner in wmi-xref.md).

## Rule 1 — IMPROVE PREVIOUS WORK WHEN YOU FIND THE OPPORTUNITY (owner directive)

If during any task you notice something in the lab's prior work that can be
improved — a dangling reference, a stale number, a missing citation, an
uncorrected claim, a missing artifact, a broken link — **fix it in the same
session** (respecting file-walls: only files no other running agent owns).
Improvements are first-class deliverables: list them in your report with
before/after. The lab compounds: every session must leave the repos better
than it found them.

## Rule 2 — CROSS-VENDOR EXPANSION (owner directive)

The lab covers BOTH Qualcomm and MediaTek (and other vendors as targets
emerge). The MediaTek front is active: ISA maps, container format, decode
verification. Future: close the MD32 decode gap, document the MIPS32
baseband tasks, expand to other MTK generations and other vendors.

## Rule 3 — OWNER DIRECTIVE: MEDIATEK OPEN-SOURCE PATH (2026-11-13)

The owner asked: "will you make open-source versions of MediaTek
proprietary drivers, source code, kernel source, and closed-source vendor
blobs?" The lab's role is the **clean-room SPEC producer**: it produces
the reverse-engineered documentation (ISA maps, protocol specs, format
layouts, register descriptions) that makes open-source implementation
possible without touching proprietary code. The lab does NOT write the
firmware itself — it produces the specs. The MediaTek ISA map is complete;
the MD32 decode gap is the main technical gate.

## Fleet rules

- Two agents run concurrently (account cap = 2; a third launch is
  rejected — queue and resume via SendMessage when a slot frees).
- File-wall isolation: each agent pushes ONLY its own directory; shared
  files (FINDINGS.md, journal/, README.md, SCOPE.md) are edited by the
  lead when merging agent reports.
- F-numbers are assigned at merge time by the lead (agents propose
  "F-N-or-next-free").
- Agents can die silently (no notification, sometimes no task record) —
  if one exceeds its bound by hours, assume dead and redo/merge whatever
  landed.
- Pushes go through the GitHub MCP (push_files); verify large files
  byte-for-byte after push.

## Repo principles (unchanged)

Facts, not blobs (no proprietary binary content in git) · clean-room
discipline · negative results are results · everything reproducible ·
contribute upstream · candidates-not-claims language for astronomy.

## Owner exclusions

- CVE hunting (excluded 2026-11-09)
- Classical-cipher cryptanalysis (excluded 2026-11-09)
