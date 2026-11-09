# Open Discovery Lab

Original research, recorded openly. The goal is **not** to re-implement things
that already exist — every track here targets a *verified gap*: something the
relevant community needs, that nobody has published yet.

This repo is the permanent lab notebook. Findings, negative results, methods,
and raw derived data all live here.

## Tracks

| Track | Domain | The verified gap | Status |
|-------|--------|------------------|--------|
| **A — Android Blobs** | Reverse engineering for [LibrePhone](https://www.fsf.org/news/librephone-project) (FSF, upstream: [Codeberg/rsavoye/librephone](https://codeberg.org/rsavoye/librephone)) | No free public documentation exists for Qualcomm Hexagon/qdsp6 & WCN6750 wpss firmware internals; upstream is in analysis phase with thin per-segment docs | 🟡 active |
| **B — Sky Mining** | Mining public astronomical survey data (Gaia DR3 / ZTF / WISE) | Public-data mining demonstrably discovers uncatalogued objects (3,006 new brown dwarfs via Backyard Worlds, May 2026); uncatalogued high-proper-motion sources remain | 🟡 active |
| **C — Discovery Engine** | Finding *what* to research | No systematic tool cross-references open-problem registries (unsolved file formats, RE challenge spaces, open-data sets) against documented work to surface unique contribution targets | 🟢 bootstrapping |
| **D — Grid Ramsey Minima** | Combinatorial enumeration: minimum #monochromatic rectangles in 2-colorings of grids (OEIS [A399620](https://oeis.org/A399620) / [A399621](https://oeis.org/A399621)) | OEIS entries (2026-09-05) stop at n=8 with the `more` keyword; no paper or public code computes a(9) or row 9 — first exact values and bounds landed here | 🟡 active |

Writeups that mature into standalone documents go in [`papers/`](papers/).
Running findings are logged in [`FINDINGS.md`](FINDINGS.md). Dated lab entries
in [`journal/`](journal/).

## Principles

1. **Facts, not blobs.** No proprietary binary content is ever committed here.
   Only derived metadata: segment tables, ELF headers, string lists, hashes,
   protocol constants, documentation. Facts are not copyrightable; blobs are.
2. **Clean-room discipline** for anything that could become a reimplementation:
   documentation first, code derived only from the documentation.
3. **Negative results are results.** An attack that failed and is documented
   saves the next researcher a month.
4. **Everything reproducible.** Every finding ships with the exact script that
   produced it.
5. **Contribute upstream.** Track A work is fed back to
   [upstream LibrePhone](https://codeberg.org/rsavoye/librephone) via PRs.

## Environment

Standard Linux box: 12 cores, 15 GB RAM, ~160 GB free. Primary tools:
python3, binutils, unsquashfs, radare2-family disassemblers, self-written
parsers. Analysis targets come from public LineageOS builds (downloadable
without any hardware).

## Provenance

Research instruments (cloned famous projects used as discovery aids, never
re-published here): [awesome-rea](https://github.com/yibie/awesome-rea),
[wtsxDev/reverse-engineering](https://github.com/wtsxDev/reverse-engineering),
[Just Solve the File Format Problem wiki](http://fileformats.archiveteam.org).

## License

MIT for code. Documentation and findings: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
