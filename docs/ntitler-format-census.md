# NTitler Animation (.nt) — Format Census and Grammar Crack

Finding: F-48-proposed (Track C, R-8) — 2026-11-14
Corpus: 88 `.nt` files (all parse; none committed — samples live only in /tmp)

## What NTitler is (prior art, dated)

NTitler is an **AmigaOS m68k realtime 3D text/vector titler** by **Michiel den Outer**
(michiel@luna.nl), distributed as shareware on Aminet as `gfx/misc/ntpro`
(NTitler Pro v2.2). It renders 3D text animations over IFF backdrops with copper
effects, colour cycling and IFF sound samples, and exports to Anim5 for use in
Scala-style presentation systems. Aminet readme retrieved 2026-11-14 (v2.2,
m68k-amigaos, "Realtime 3D MultiMedia/Video Titler").

Public state of the `.nt` file grammar before this census, checked 2026-11-14:

- **dexvert** (`src/format/video/ntitler.js`): unsupported, magic `NTitler show`,
  "only 88 unique files on discmaster, all very small (most <1k)", "Couldn't locate
  a converter or extractor".
- **TrID** (`nt-show.trid.xml`, TrIDScan/Py v2.02, **2018-06-09**, FileNum 87):
  signature = ASCII `BT90` at offset 0. No grammar documented.
- No converter, extractor, spec, or source exists publicly.

Verdict: the "no converter" claim holds as of 2026-11-14; the file grammar itself
was undocumented until now.

## Corpus

Instead of chasing discmaster mirrors, the census uses the **complete shows
directory shipped with the tool itself**: `ntpro.lha` (634,634 bytes, LHA lh5,
172 entries) from aminet.net contains 88 `.nt` show files — exactly the count
dexvert reports from discmaster, presumably the same set circulating. Sizes
698–1800 bytes (median 872), Shannon entropy 1.36–4.00 bits/byte (text-driven
low-entropy binary). The archive also contains the player binaries `NTitler`
and `NTitlerNTSC` (Amiga HUNK executables), which is what made the crack cheap.

## Magic and version family

All 88 files begin with ASCII **`BT90`**. The `NTitler` binary contains a
version-dispatch chain (`cmp.l #'BT30'`…`#'BT90'` at file offset 0x4c74..0x4cc2)
with per-version handlers — so `.nt` files are the tail of a versioned family
**BT30, BT40, BT50, BT60, BT70, BT80, BT90** (BT90 = v2.2-era). Unknown versions
fall through to the error path at 0x521a.

**dexvert magic discrepancy explained**: the string `NTitler show` does **not**
occur in any of the 88 show files. It occurs only inside the `NTitler` binary
(offset 0xd090) as part of the runtime error message
`This is not a\nNTitler show file!` shown when the BTxx check fails. dexvert's
magic was evidently derived from that metadata, not from file content. TrID's
`BT90` is the real front-block signature.

## Binary evidence

The `NTitler` executable (HUNK, code hunk 0x5249 words, 4361 RELOC32 entries)
reads show files with fixed-offset field loads. Disassembled with capstone
(m68k, big-endian). Key reader sites:

| Site | What it does |
|---|---|
| 0x4e86 | `a0 = file+4`; reads 24 words into named globals ($3284..$32a6, $6752..$68f2, $6002..$6008, $695a, $5ff4, $5ffa); skips one word (offset 0x2e, reserved) |
| 0x4eee..0x5046 | `btst.b #0..#19` on the 32-bit word pair (file 0x20..0x23) — 20 effect-enable flags ($5fda, $5fde, $5fd8, $5fdc, $45ae, $45b0, $45b2, $5fe0..$5ff2, $b776) |
| 0x50f6 | word @0x32 -> $4aa0; 47 bytes @0x34 -> $4a20 (backdrop path, parsed via `bsr $87c6`) |
| 0x5118 | 30 bytes @0x64 -> $5204, **`not.b`** each byte (XOR-0xFF title string) |
| 0x5178 | 50 bytes @0x82 -> $b0d8 (font path) |
| 0x5190 | 8 x 50 bytes @0xb4, stride 50 -> $b420 sample-path slots |
| 0x51b4 | scene block @0x244: `move.w (a0) -> $9822; blt exit; lea 0x3a(a0)` — stride-58 records until a negative word |
| 0x4c74 | BT30..BT90 `cmp.l` dispatch chain |

## File layout (BT90, big-endian)

```
0x000   4   magic "BT90"
0x004  48   24 x u16 header words w0..w23
              w0..w8   byte-range params (0..255; likely colours/levels)
              w9..w13  28..1000 (speeds/percentages)
              w14..w15 32-bit effects bitmask (bit n = effect n enabled)
              w16..w20 params (w19: 637..1600, default 0x640=1600 in code)
              w21      skipped by reader (reserved)
              w22..w23 params
0x034  47   backdrop IFF path, NUL-terminated (PROGDIR:Backdrops/*.IFF; empty in 22/88)
0x063   1   unassigned byte (00 in corpus)
0x064  30   title/author string XOR 0xFF ("Michiel Den Outer" in all 88 files)
0x082  50   font path (PROGDIR:Fonts/{Plain,Straight,Clear,Freaky}.NFont)
0x0b4 400   8 x 50-byte sample-path slots (PROGDIR:Samples/*.SAM)
0x244 58*N  scene records (stride 58), then u16 0xffff terminator
EOF-2   2   terminator; file ends exactly here (88/88)
```

**Law verified on all 88 files**: `filesize == 0x244 + 0x3a*N + 2` with every
scene record's first word < 0x8000.

### Scene record (58 bytes)

| Off | Type | Meaning (observed) |
|---|---|---|
| +0x00 | u16 | word0 -> $9822 (0x0000 on first record; 0x0096 etc. later) |
| +0x02 | 5 x s16 | motion deltas (e.g. 602, -300, -1379, -624, -320) |
| +0x0c | 2 x u16 | params (zero in sampled records) |
| +0x12 | u16 | e.g. 151 |
| +0x14 | u16 | param |
| +0x16 | u16 | e.g. 640 (PAL hires line count — position/width?) |
| +0x18 | u16 | param |
| +0x1a | 32 B | scene text, NUL-padded; **`@` = line break** |

Decoded scene text is fully meaningful: `Anim 5@Export !`,
`use@IFF Pictures@as backdrops`, `24 bit@Copper@Effects`,
`THANKS FOR@WATCHING@THIS DEMO` — multi-line 3D captions.

### Known artifact

Several v2.2 show files store sample paths with the slot's first byte `0x00`
and the path missing its first character (`ROGDIR:Samples/Bang.SAM` instead of
`PROGDIR:Samples/Bang.SAM`); other files store complete paths at slot+0. Likely
a save-time artifact of the v2.2 saver; noted, not explained.

## Validation

`nt_decode.py` (this directory) implements the grammar. On all 88 corpus files:
magic check, header word read, XOR-0xFF title (88/88 = "Michiel Den Outer"),
string table extraction, scene-walk termination and the EOF law all pass —
88/88, 600 scene records total. A decoder emitting scene text + paths +
per-record words is therefore trivially possible (partial renderer: text and
asset lists recoverable; 3D vector rendering needs the .NFont format, out of scope).

## Open items

1. Semantic labels for header words w0..w8 (byte-range values) and scene sub-words.
2. Bit-to-effect-name mapping for the 20-flag effects bitmask (UI strings live in
   `NT.English`, 46 KB locale file, not yet correlated).
3. Older BT30..BT80 handler variants (0x4d1a..0x4e84) unmapped; no old-version
   files in this corpus.
4. Sample-slot leading-NUL artifact root cause.

## Reproduction

- Samples: `curl -o ntpro.lha https://aminet.net/gfx/misc/ntpro.lha` (never commit).
- Disassembly: capstone `CS_ARCH_M68K, CS_MODE_BIG_ENDIAN` on the `NTitler` hunk.
- Decode: `python3 -I nt_decode.py <files...>`.
