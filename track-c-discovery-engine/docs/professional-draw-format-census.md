# Professional Draw (Amiga) .clips / .pdraw — format census (F-37, Track C, R-6)

Census date: 2026-11-12. Samples: NOT committed (all in /tmp only).

## Prior art (Rule 0, dated 2026-11-12)

- dexvert `src/format/image/professionalDraw.js` (repo SHA b126fe4f, checked 2026-11-12): `unsupported = true`, notes `"No known converter."`, comment: "candidate for future vibe coding, 746 unique files on discmaster. But I'd want to seperate out detection of clip/document/page as each is likely a different file type?" magic strings: "Professional Draw clip/document/page". ext `.clips`.
- Web search 2026-11-12: no converter, no spec, no RE write-up found. DigiPres/Wikidata confirm `.clips` as the Professional Draw clipart extension. Software background: Amiga drawing package (v3.03 per sample header; CU Amiga Mar 1992 covers it).
- VERDICT: dexvert's "no known converter" note is CURRENT as of 2026-11-12. This census is the first public structural description we located. dexvert's hunch is confirmed: clips and document/page ARE different containers (below).

## Samples

10 files from `https://sembiance.com/fileFormatSamples/image/professionalDraw/`: Birds (7.8 KB), RibbonBorder (1.2 KB), Tennis (3.3 KB), Christmas (70 KB) — extensionless but PDPF; Logo.clips (228 KB), MUS.clips, PER.clips, REF.clips; TriplePlay2.pdraw (562 KB), TriplePlay2PCB.pdraw (601 KB).

## Census findings — clip files (`PDPF` container, 8/8 samples)

- **Header (cracked)**: ASCII `PDPF` + u32be total file size. Verified **exact match with file size in 8/8 samples** (7774, 70228, 228346, 18466, 80296, 82756, 1238, 3338).
- **Chunking (cracked)**: flat IFF-style stream: 4CC + u32be payload size, no padding/alignment. **8/8 files parse with zero anomalies and 100% byte coverage** (35–7658 chunks/file, 19–22 chunk types).
- **Section brackets**: zero-length marker chunks delimit sections, terminated by matching `*FIN`/`*FN` chunks:
  - Color table: `COLR`(0) ... `CFIN`(0). Per color: `COLR`(0) + `CNAM` (NUL-padded name: "Black", "Grey 33%", "Blue", "Flesh", "Red", "Yellow", "White", "Magenta", "Cyan", "PANTONE 265 CV") + `SRGB` (u16be r,g,b at 0x0F=1.0 scale + 2 pad bytes) + `PYMC` or `YMCK` (u16be C,M,Y,K) + `CFLG` (2B) + `CSCR` (4B) + optional `FSCR` (8B).
  - Clip definitions: `CLIP`(0) ... `OFIN`(0), file ends with `CLFN`(0). Per clip: `CLIP`(0) + `CLNM` (name) + `VBOX` (u32be x1,y1,x2,y2) + `DBOX` (s32be x1,y1,x2,y2) + objects.
  - Object: `OBJ ` (4B payload = object type: **`BEZ4`** bezier or **`CIRC`** circle) + `VBOX` + `DBOX` + `OFLG` (4B) + `LINE` (8B) + `FILL` (2B) + `DATA` (variable, 146–506 B in Birds) + `OEND`(0). `STXT` objects (Logo.clips: 144) are fixed 18-byte records (4 s32be + u16? — meaning unresolved).
- **Extracted clip names prove semantic decode**: Birds=1 clip "Finch"; Christmas=11 ("Wreath", "Bells", "Bow", "CandyCane", "FinePlace", "NorthPole", ...); Logo.clips=8 ("CDTVlogo_30", "CDTVlogo_7", "CDTVlogo_5.5", "CDTVlogo_3.5", + `B` variants — official CDTV logo art at multiple sizes); MUS/PER/REF.clips=15 each ("MUS_1", "PER_1.5", "REF_10", ... — symbol libraries in size variants); Tennis=2 ("TennisBall", "TennisCourt"); RibbonBorder=1.
- **VBOX coordinates**: u32be quads, values 11,139–806,912 across files; consistent with a fixed-point unit (16.16 hypothesis: RibbonBorder 611840x806400 ≈ 9.34"x12.31"; MUS_1 ≈ 0.18") — hypothesis, not verified against a known page size.
- **`DATA` (partial)**: byte pairs span the full u16 range (max observed 64,769 ≈ 0xFFFF) — consistent with normalized/fixed-point point coordinates, but the point grammar (on-curve vs control points, poly/quad/cubic) is unresolved.

## Census findings — document files (`.pdraw`, 2 samples)

- **Different container (confirms dexvert's clip/document split)**: header `08 08 09 0F` + NUL-terminated `Professional Draw V3.03` + zero padding; four u32be invariants at unaligned offsets = **(3000, 198, 72, 102), identical in both documents** (meaning unresolved — plausible page/metric fields; 72 suggests a DPI field).
- Then P-chunks in the same 4CC+u32be scheme: `PENV` (1614 B pen/environment table) + `PDOC` + `PPAG` x2 + `PBOX` + `PSGR` — then the walk stops on non-4CC data inside the page body (0xa84 / 0xa6c): page sub-structure uses a different layout (partial — honest negative).
- `PENV` payload starts `0200 0101 0100 0006 0000 0001 0000 0000 fffe 7623 ffff efeb f000 014d...` — pen/style defaults + `0046/b400 0046/f000` fraction pairs like the clip files' `FSCR`.

## Crack verdict

- RESOLVED: clip container (PDPF magic, size self-check, chunk scheme, section brackets, color records, clip/object framing, clip names, object types BEZ4/CIRC).
- PARTIAL: BEZ4/CIRC DATA point grammar; VBOX unit; STXT record; .pdraw header field meanings + page body.
- NEGATIVE: no renderer (bezier semantics unresolved); .pdraw documents not fully walkable.

## Decoder

`results/format-re/professional-draw-census/pdclips_decode.py` (stdlib Python): validates PDPF size self-check, walks chunks, extracts palette (names + 8-bit RGB + CMYK), clips (names, VBOX/DBOX), objects (type, flags, line width, fill, DATA length), and decodes .pdraw headers + top-level chunks. Validation (`professional-draw-census/pdclips-validation.json`): 8/8 .clips byte-exact, 2/2 .pdraw headers + top chunk lists.

## Next steps

- Crack BEZ4 `DATA`: dump one small object (RibbonBorder, 2 objects) and test 2x u16be point interpretation against VBOX normalization; compare rendered polygon silhouette with the clip name.
- Verify VBOX unit against known CDTV logo aspect ratio (Logo.clips variants _30/_7/_5.5/_3.5 should scale linearly).
- .pdraw: locate `PPAG` body offset table (the 3000/198/72/102 header may be an offset/dimension array).
