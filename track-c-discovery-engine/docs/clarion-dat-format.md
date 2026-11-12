# Clarion Database .DAT — census + header crack (R-3, 2026-11-12)

Track C queue item R-3 ("Clarion Database File", .dat). Companion raw census:
`results/format-re/clarion-dat/clarion-dat-census.json` (49 files, per-file parsed header
+ descriptors). Decoder: `results/format-re/clarion-dat/clarion_dat_decode.py`
(stdlib Python, validated on the full corpus).

## Claim (with Rule-0 correction up front)

The queue entry for R-3 inherited dexvert's note "Did a Google search, couldn't
find anything about it". **Rule 0 check refutes zero-documentation**: the legacy
Clarion .DAT layout IS documented — a Russian-language article on
clarionlife.net ("Clarion DAT файл", undated, read 2026-11-12; describes
Clarion Professional Developer v2-era files, i.e. late-1980s/early-1990s) gives
the full header/descriptor/record layout, and comp.lang.clarion threads (Google
Groups archive) discuss conversions against it. Tools exist that read the
format (clariondbreader on SourceForge; commercial DataMeans / AETL Clarion
readers). What is NOT documented publicly at byte-validation level: the
encryption scheme, exact slot-allocation semantics, and no public
spec-validation across a corpus. So the honest claim is **independent
validation + extensions**, not first documentation:

- Validated the published layout against 49 files with exact arithmetic
  (three identities, 43/43 below) — first public corpus validation we know of.
- Extended the spec with corrections/undocumented details (list below).
- Cracked the file encryption for 2 of 6 encrypted samples (2-byte periodic
  XOR, per-section keystream reset) — not part of the published spec.
- TPS boundary: .TPS (TopSpeed, Clarion 3.5+/Windows era) is a different,
  partially documented format (CapSoft driver docs, third-party TPS tooling).
  Nothing here applies to TPS. This corpus is the legacy ISAM "Clarion files"
  era (.dat + .k??/.mem companions).

dexvert's own module (`Sembiance/dexvert` src/format/document/clarionDatabase.js
@ b126fe4) detects by magic string "Clarion 2 DataBase for DOS" and is
`unsupported = true` ("5,548 unique files on discmaster, but just decided to
pass on vibe coding a converter"). Notably the magic STRING does not appear in
any of our 49 samples — all 49 use the binary signature 0x3343 (two signature
generations; the string form is presumably Clarion 2.0 era).

## Method

All 49 files from `sembiance.com/fileFormatSamples/document/clarionDatabase/`
(46 .dat + 3 .fil) fetched to /tmp, 2026-11-12. Header parsed per the
clarionlife.net layout, cross-file invariants measured, arithmetic identities
tested, field/key/picture/array descriptors walked, records decoded and
spot-checked against content, entropy mapped, 6 sfatr-encrypted outliers
attacked with keystream hypothesis testing. MEMO companion structure checked
on 2 fetched .MEM files.

## Layout (validated)

All multi-byte LE. Header 85 bytes (0x00–0x54):

| Off | Field | Size | Notes from corpus |
|-----|-------|------|-------------------|
| 0x00 | sig | 2 | `43 33` ("C3") = 0x3343 — 49/49 |
| 0x02 | sfatr | 2 | bitfield; high byte always 0 |
| 0x04 | numbkeys | 1 | 0–6 (43 plain files) |
| 0x05 | numrecs | 4 | = highest record number ever allocated = physical slots |
| 0x09 | numdels | 4 | deleted slots (4 files nonzero) |
| 0x0D | numflds | 2 | 1–38 observed |
| 0x0F | numpics | 2 | picture token count |
| 0x11 | numarrs | 2 | array count |
| 0x13 | reclen | 2 | record slot length incl. 5-byte record header |
| 0x15 | offset | 4 | byte offset of data area (= end of descriptors) |
| 0x19 | logeof | 4 | record-number (not byte) bounds of live range |
| 0x1D | logbof | 4 | ditto (corpus: 0/1..numrecs) |
| 0x21 | freerec | 4 | first free-listed (deleted) record number |
| 0x25 | recnam[12] | 12 | record name, space-padded (zeros also seen) |
| 0x31 | memnam[12] | 12 | memo file name, zero-filled when absent |
| 0x3D | filpre[3] | 3 | file prefix ("APP", "BBR", …) |
| 0x40 | recpre[3] | 3 | record prefix |
| 0x43 | memolen | 2 | memo length |
| 0x45 | memowid | 2 | memo width |
| 0x47 | reserved | 4 | 0 |
| 0x4B | chgtime | 4 | centiseconds since midnight −1; 43/43 in valid range 1–8640000 |
| 0x4F | chgdate | 4 | days, epoch 1801 (+3 day skew > 36527); 43/43 valid → **1989-07-17 … 1992-05-14** |
| 0x53 | reserved2 | 2 | 0 |

Then: `numflds` × 27-byte field descriptors (type u8 [1=LONG, 2=REAL, 3=STRING,
4=STRING+PICTURE, 5=BYTE, 6=SHORT, 7=GROUP, 8=DECIMAL], name[16]
space-padded, foffset u16, length u16, decsig u8, decdec u8, arrnum u16,
picnum u16); keys (19-byte KEYSECT + 6-byte KEYPART × numcomps); pictures
(**2 + piclen** bytes — see corrections); arrays (6 bytes + 4 bytes per
dimension). Records: numrecs slots of reclen bytes = 5-byte record header
(rhd u8 bitfield, rptr u32) + data. DECIMAL = packed BCD, 2 digits/byte
(decsig = digit count — CRDTCARD ISSNUMB decsig=13 → 7 bytes 0x00001234567890).
LONG/SHORT/REAL little-endian, strings space-padded, no separators.

## Cracked / validated identities (the PVD pattern)

Held across **43/43 non-encrypted files** (zero exceptions):

1. `descriptor end == offset (data area start)` — exact for all 43.
2. `offset == 0x55 + 27*numflds + key/picture/array descriptor sizes` — 43/43.
3. `filesize == offset + numrecs * reclen` — 43/43. **Slot semantics
   established:** numrecs is the highest record number ever allocated and
   equals the physical slot count; deleted slots are reclaimed in place
   (sfatr bit 5 "reclaim-deleted" set in 42/43 — APPOINTS.DAT is the
   exception), numdels counts free-listed slots among them, freerec chains
   the first one. The naive
   `offset + (numrecs+numdels)*reclen` fails exactly on the 4 files with
   numdels>0 — deleted records do not occupy extra slots. (The naive formula
   coincides with the correct one for the other 39.)
4. chgtime/chgdate decode to valid wall-clock dates for 43/43 (1989–1992,
   consistent with the format's era).

Record-level decode validated by content: BBRAND.DAT → bullet brands
(Penn/Hornady/Speer/Sierra/…), CRDTCARD.DAT → Visa/Hess's/Amoco + issuer
strings, APPOINTS.DAT → LONG dates 69235–69306 ≈ 1990, matching header dates.

## Corrections/extensions to the published spec

1. **rhd bit semantics**: clarionlife lists bits 0=new, 1=old, 2=revised,
   4=deleted, 6=held. The corpus (bit 4 = 0x10 present in exactly the 4
   numdels>0 files' deleted slots, e.g. CRDTCARD slot 4 = 0x11) confirms these
   are **bit numbers** — value 0x10 = deleted, value 4 (0x04) = revised flag on
   live records. Values seen: 1, 2, 5, 17, 18, 21, 22.
2. **Picture descriptors are 2 + piclen bytes, not 2 + 256.** Fixed-size
   parsing overshoots the data area by 204–468 bytes in 7 files; piclen-sized
   parsing gives exact descriptor-end == offset in all 43.
3. **Array descriptors with numdim == 0 still carry one ARRPART** (4 bytes);
   use totdim for the dimension count then. Without this, APPOINTS.DAT's
   descriptor end misses the data start by 4.
4. **logbof/logeof are record numbers**, not byte offsets (e.g. CRDTCARD
   logbof=1/logeof=3 with 4 slots, one deleted; HHNAMES logbof=5/logeof=7).
5. **.FIL files are the same format** — CATS.FIL, DATES.FIL, NAMES.FIL parse
   identically to .DAT.

## Encryption (partial crack — honest boundary)

6 of 49 files set sfatr bits 1|2 ("owned"+"encrypted"): DEFAULT, GENESOFT,
GEORGEA, GEORGEE, GEORGEX, HHCNTRL. Their bytes from 0x04 onward are
key-scrambled (sig + sfatr survive in clear).

- **Cracked (2/6):** whole-header structure resolves under a 2-byte periodic
  XOR with per-file key, anchored at 0x04, with **keystream phase reset at
  each section boundary** (header @0x04, each 27-byte field descriptor @0x55+27i,
  presumably each descriptor record). GENESOFT.DAT key `d3 c6` → 12 STRING
  fields GEN:SOIFXCFRJ…GEN:PASSWORDS (a password table; offsets 0/20/37/…/161,
  sum 181 + 5 = reclen 186 exactly). GEORGEA.DAT key `3e 3a` →
  ATH:AUTHOR/ADDRESS1/ADDRESS2/TITLE/PASSWORD (offsets 0/32/64/96/128,
  140 + 5 = reclen 145 exactly). Keys are per-file (password-derived).
- **Not cracked (4/6):** DEFAULT (`sfatr 0x66`), GEORGEE/GEORGEX (`0xa6`),
  HHCNTRL (`0x26`) fail all ≤2-byte repeating keys under the section-reset
  model — longer keystreams; brute force not attempted beyond 2 bytes.
- **Detection signal:** encrypted files' whole-file entropy is only 4.3–5.2
  bits/byte (vs 0.96–4.49 plain) — a 2-byte periodic XOR preserves byte-period
  structure, so these are detectable (and, where cracked, decryptable) by
  periodicity analysis, not by entropy alone.
- Record-bodies of the two cracked files use a different phase/keystream than
  their descriptors — record-level decryption left open (rhd/rptr of decoded
  records come out implausible: GENESOFT rec1 rhd=0xD2).

## Entropy map (plain files)

Whole-file 0.96–4.49 bits/byte — fixed-length slots of space-padded ASCII with
BCD numerics (no compression observed anywhere; sfatr bit 4 "compressed" never
set). Header/descriptor region low-entropy; no high-entropy regions in any
plain file.

## Honest negatives / open

- Key-file (.K??/.I??) layout not exercised — no .K samples in the mirror set
  (clarionHelp/ .HLP and clarionMemo/ .MEM exist; .MEM checked, matches the
  published "M3" + 256-byte block structure on 2 samples).
- comptype bit meanings (observed 0/16/32/48/64/96/97/112) not decoded beyond
  the spec's "key vs index / duplicates / case-insensitive" hint.
- rptr semantics for non-deleted memo records (APPOINTS shows rptr = 1..4 on
  live records with a memo attached — presumably memo block pointers) inferred,
  not proven against a .MEM file.
- dexvert's "Clarion 2 DataBase for DOS" string-magic generation not
  represented in this corpus (all 49 are 0x3343).
- The 4 uncracked encrypted headers need keystreams > 2 bytes.

## Instrument provenance

- sembiance.com/fileFormatSamples/document/{clarionDatabase,clarionMemo}/
  listings + 49 + 2 files fetched 2026-11-12 (49 .dat/.fil; .MEM not committed).
- clarionlife.net "Clarion DAT файл" (Russian; undated; read 2026-11-12 via
  fetch+translation) — the primary prior-art layout source.
- dexvert src/format/document/clarionDatabase.js, packed.js, WEAK.js @ b126fe4
  (GitHub code search, 2026-11-12).
- CapSoft "Clarion Object Based Database Drivers" docs (DAT vs TPS boundary),
  Google Groups comp.lang.clarion threads, SourceForge clariondbreader
  (existence checks, 2026-11-12).
- WebSearch: "Clarion .dat file format legacy", 2026-11-12.
