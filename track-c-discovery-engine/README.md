# Track C — Discovery Engine

**Mission:** systematically find *what* is worth researching — turn "search
the whole internet for something unique" from a one-off into a repeatable
pipeline that scores open problems by novelty, feasibility, and value.

## Instrument sources (cloned under `../../instruments/`, never re-published)

- [awesome-rea](https://github.com/yibie/awesome-rea) — AI-assisted RE
  project index (game decompilation, static recompilation, tooling).
- [wtsxDev/reverse-engineering](https://github.com/wtsxDev/reverse-engineering)
  — general RE resource index.
- [awesome-infosec](https://github.com/onlurking/awesome-infosec).
- [Just Solve the File Format Problem](http://fileformats.archiveteam.org)
  — the canonical registry of file formats with missing documentation;
  pairs with [dexvert samples](https://github.com/Sembiance/dexvert) which
  provides sample files for obscure formats.

## Pipeline

1. **Harvest:** pull open-problem registries (JSIT categories such as
   "Format information missing"; awesome-list entries marked as
   undocumented/unknown; open-data portals; open-problem wikis).
2. **Deduplicate & score:** novelty (is there any public documentation or
   tool? — checked via GitHub code search + web search), feasibility (are
   samples/files obtainable? format complexity), value (who needs it —
   preservation bodies, forensics, interoperability).
3. **Publish:** `targets.md` — the scored queue, updated per session.
4. **Feed:** high-scoring targets spawn work in Track A (blobs) or new
   tracks; completed targets get documented back to JSIT/wiki pages.

## Current scored queue

See `targets.md` (first harvest in progress — JSIT "format information
missing" categories + dexvert samples cross-check).
