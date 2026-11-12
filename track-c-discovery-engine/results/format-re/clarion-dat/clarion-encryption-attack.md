# Clarion .DAT header encryption — complete crack (F-39, 2026-11-12)

Companion to F-38's `docs/clarion-dat-format.md` (R-3). F-38 cracked the headers of
2 of the 6 sfatr-encrypted samples (GENESOFT `d3c6`, GEORGEA `3e3a`) and reported
the remaining 4 (DEFAULT, GEORGEE, GEORGEX, HHCNTRL) as needing keystreams > 2 bytes.
**This follow-up cracks all 6/6 — the remaining four are the same 2-byte periodic XOR
with per-section phase reset — and extends the crack from headers to record bodies.**
Raw evidence JSON: `results/format-re/clarion-dat/clarion-encryption-keys.json`.
Sample bytes were fetched from the same sembiance.com mirror set to /tmp only and are
not committed (sizes match the F-38 census exactly).

## Claim

1. **All 6 encrypted headers are cracked** with 2-byte per-file XOR keys:

   | file | sfatr | key (k0 k1) | status in F-38 | what the decrypted file is |
   |------|-------|-------------|----------------|----------------------------|
   | DEFAULT.DAT | 0x66 | **d8 c6** | not cracked | app defaults/timeclock table (98 fields) |
   | GENESOFT.DAT | 0xe6 | d3 c6 | cracked (F-38) | password table, 12 STRING fields |
   | GEORGEA.DAT | 0x86 | 3e 3a | cracked (F-38) | author card "George Tanner / GEORGE'S JOURNAL" |
   | GEORGEE.DAT | 0xa6 | **3e 3a** | not cracked | journal entry index, 29 slots / 12 live |
   | GEORGEX.DAT | 0xa6 | **3e 3a** | not cracked | journal entry text, 38 slots |
   | HHCNTRL.DAT | 0x26 | **50 56** | not cracked | control record: serial, vendor, phone-access words |

2. **F-38's negative claim is refuted by exhaustive search**: "fail all ≤2-byte
   repeating keys under the section-reset model — longer keystreams". A brute force
   over all 65,536 two-byte keys per file, scored on the F-38 arithmetic identities
   (reserved 4 bytes at 0x47–0x4A == 0; `filesize == offset + numrecs*reclen`;
   `offset ≥ 0x55 + 27*numflds` with plausible key/picture/array extras; valid
   chgtime/chgdate; printable name fields), returns **exactly one fully-valid key per
   file** (63/63 checks). Regression: the same search reproduces F-38's two known keys
   uniquely (GENESOFT→d3c6, GEORGEA→3e3a), so the scoring is calibrated, not
   over-fit. GEORGEE/GEORGEX share GEORGEA's key `3e3a` (same application/password —
   GEORGEA = author card, GEORGEE = entries, GEORGEX = entry text); DEFAULT `d8c6`
   and HHCNTRL `5056` are independent.

3. **The encryption mechanism is now characterized end-to-end** (upgrade of F-38's
   partial model):
   - Cipher: 2-byte repeating XOR, per-file key (k0, k1). Plaintext byte at even
     keystream index XORs k0, odd index XORs k1.
   - Keystream index resets to 0 at **each section boundary**: the header body at
     0x04 (sig `43 33` + sfatr at 0x02 are stored clear), each 27-byte field
     descriptor at 0x55+27i, each 19-byte KEYSECT, each 6-byte KEYPART, each
     picture/array section. F-38 observed the header+descriptor part of this; we
     confirm it and show it holds for key/picture/array sections too.
   - **Record slots (new — closes F-38's "record-level decryption left open")**: the
     5-byte slot header (rhd u8, rptr u32) is stored **clear**; the record body is
     XORed with the same per-file key with phase reset at the body start (body byte
     j uses k0 at even j). Evidence: all 6 files' slot headers read `rhd 0x01/0x05`
     (live) or `0x11/0x15` (deleted bit 4 set) with rptr=0 on live slots — exactly
     the plain-corpus rhd value set {1,2,5,17,18,21,22} — and bodies decode to
     ASCII/BCD/binary per their field descriptors.
   - KEYPART internal layout (extension to the published spec, validated on plain
     BBRAND.DAT raw bytes + all 4 encrypted key sections):
     `KEYSECT(19) = ncomp u8, name[16] space-padded, ktype u8, klen u8`;
     `KEYPART(6) = ftype u8, fldno u8, rfu u8, foffset u16 LE, flen u8`.
     (F-38's census parsed key names from offset 0 — plain files' names actually
     start at byte 1; byte 0 is the component count.)

4. **Recovered content** (decoded facts only; no ciphertext committed):
   - DEFAULT.DAT: 98-field defaults record — OVERRIDE=Y, PWDEXIT=Y, DEDUCT=N,
     LUNCH=60.0 min, MAXHOUR=7.0, area code 000, and a 3-week × 5-workday schedule
     (WD1..WD5 INDAY/LCHDAY/OUTDAY = MO/TU/WE/TH/FR, INTIME 2880001 cs = 08:00:00.01,
     LCHTIME 4320001 = 12:00:00.01, OUTIME 6120001 = 17:00:00.01; weeks 2–3 blank).
   - GENESOFT.DAT: password table. GEN:PASSWORDS = `psdjxczny`; companion fields hold
     `ooqwxsqde`, `asmnjuwrt`, `weuyhbnvc`, `qawsedrft` (keyboard-walk), and
     GEN:DKAPMBHSL = `shareware` (license-state field).
   - GEORGEA.DAT: ATH:AUTHOR "George Tanner", ADDRESS1 "123 Main Street",
     ADDRESS2 "Anywhere, USA", TITLE "GEORGE'S JOURNAL", ATH:PASSWORD empty.
   - GEORGEE.DAT: 29 slots, 17 deleted (numdels=17 exactly). Live entries include
     "NEW YEAR'S DAY" (date 69400 = 1991-01-01), "REPORT CARDS" (1991-01-10),
     "RIDE IN THE VAN" (1991-01-12), "A NEW MONTH" (1991-02-01), "CAMPING TRIP"
     (1991-05-18, written the morning after "Friday night" camping), "BACK TO WORK"
     (1991-01-02), …, "SPRING BEGINS" (69479 = 1991-03-21, the equinox). TIME fields
     are centiseconds-since-midnight (07:39–22:26).
   - GEORGEX.DAT: 38 slots of journal text (TXT:NTRYREC links to the GEORGEE entry
     number, TXT:TEXTNUM = part number), e.g. entry 7 "CAMPING TRIP" has 4 parts:
     "We went on a camping trip on Friday night. …" / "hard time sleeping on the
     ground. I told the kids some scary stories…" / "The next morning we went for a
     hike. We found a nice tarzan-swing type vine that we played on for hours."
   - HHCNTRL.DAT: HHC:SERIAL_NO = "S10000004", NOTICE = "  Copyright 1990 Torbert
     Data Systems, INC.", and six per-screen access words: HHC:PWORD="Police",
     FWORD="Fire", AWORD="Ambulance", DWORD="Doctor", PEWORD="Pediatrician",
     POWORD="Poison", with BCD phone numbers (POLICE/FIRE/AMBULANCE = …091 = 911;
     DOCTOR = 454232×; OTHERNAME1/2 = "Power Company" 434567×, "Gas Company"
     545678×), HHC:REGISTERED = "p".

## Method

1. Fetched the 6 encrypted + 4 plain samples from the F-38 mirror to /tmp; verified
   plain files' reserved bytes (0x47–0x4A, 0x53–0x54) are zero and re-verified F-38's
   two cracked keys reproduce valid headers (regression).
2. Exhaustive brute force: for each file, all 65,536 (k0,k1) pairs applied to the
   81-byte encrypted header region (0x04–0x54), scored on: reserved 4 bytes == 0
   (weight 12 — kills ~99.998% of keys alone), filesize identity (weight 14),
   extras-window consistency `0 ≤ offset − (0x55+27·numflds) ≤ key/pic/arr budget`
   (weight 8), field-count/reclen/logeof/logbof/freerec/chgtime/chgdate ranges,
   printable name fields. One scoring iteration was needed: DEFAULT has numflds=98,
   above the initial 64 cap informed by the plain corpus (1–38); relaxed to 128, the
   filesize identity then holds exactly (2731 = 85 + 27·98; 2731 + 1·306 = 3037).
3. Decoded all 6 files fully: header, per-descriptor phase-reset field tables
   (all type bytes in 1–8, names printable), key sections, record slots under the
   clear-header/encrypted-body model, BCD decimals, LONG dates (epoch calibrated on
   plain CRDTCARD 69236 = 1990-07-21) and centisecond times.
4. Cross-validations: GEORGEE's 17 deleted slots = numdels and chain from freerec;
   GEORGEX NTRYREC values match GEORGEE entry numbers (e.g. entry 7 ↔ slots 28/35/36/37);
   HHCNTRL BCD "…091" = 911 under PWORD="Police".
5. **Date-epoch pin (sharpens F-38)**: F-38's doc says chgdate is "days, epoch 1801
   (+3 day skew)". The exact epoch is **1800-12-28** — the documented Clarion
   "standard date" — verified two independent ways: 69236 → 1990-07-21 matches the
   census anchor (CRDTCARD), and the decrypted GEORGEE entries land on semantically
   correct weekdays: all three "CHURCH*" entries on Sundays (1991-01-06, 01-27,
   05-19), "MOW THE LAWN DAY"/"ACTIVITY DAY"/"CAMPING TRIP" on Saturdays,
   "BACK TO WORK" on Wed 1991-01-02 (day after the holiday), "THE BEGINNING OF
   MARCH" on 1991-03-01, "SPRING BEGINS" on the 1991 equinox 03-21.

## Honest negatives / open

- **reserved2 (0x53–0x54) anomaly**: under the correct keys, these 2 bytes decrypt to
  non-zero in all 6 encrypted files (DEFAULT 9bd1, GENESOFT 2cd9, GEORGEA 2337,
  GEORGEE 5d39, GEORGEX 6a39, HHCNTRL 9557) while both reserved fields are zero in
  all 43 plain files. No simple checksum (sum/xor of the decrypted header) matched.
  Either encrypted-file writers leave garbage there, or these bytes carry an
  unknown per-file marker. Does not affect the crack (every other identity holds).
- **klen byte in KEYSECT**: decodes to 22/58/81 on GEORGEE/GEORGEX/HHCNTRL — not the
  sum of component field lengths (40/4/1), while plain BBRAND's klen (15) does equal
  its component length. Semantics unresolved (possibly an index/keyfile-related
  size). ncomp, name, ktype and KEYPART ftype/fldno/foffset/flen all decode
  consistently, so the section phase is right.
- **Password→key derivation unknown.** Keys are per-file; the GEORGE* trio shares
  `3e3a` (same password), DEFAULT/HHCNTRL differ. The plaintext passwords that
  generated them are not recoverable from the keys themselves (GEORGEA's
  ATH:PASSWORD is empty; GENESOFT's table lists candidate passwords but which one
  maps to which file/key is unproven). Recovery of *any* future file still costs one
  65,536-candidate brute force (~instant) against the arithmetic scoring, so the
  derivation question is moot for data recovery.
- Record bodies of GEORGEE contain binary LONG date/time values whose epoch/unit we
  did not independently re-derive beyond the calendar check above (69400 =
  1991-01-01 matches "NEW YEAR'S DAY").
- Trailing-byte quirks, characterized: DEFAULT's last field DEF:WD5OUTIME3 decodes
  to 0 in its first 3 bytes with the file's final byte being a literal unencrypted
  0x00 at EOF (fill/terminator outside the keystream) — the field value is 0
  (blank), not the -671088640 a naive 4-byte read gives. GEORGEX TEXT fields carry
  a 0xFF end-of-text marker before the space padding (e.g. "…last night.\xFF"),
  and GENESOFT's last string ends 0xF3 — app-level fill bytes inside the encrypted
  body, not keystream anomalies.
- KEYSECT key names on the GEORGE* files ("DATEKEY", "NAMEKEY", "TEXTKEY") decode
  with a leading component-count byte (3/3/2) that matches their KEYPART counts —
  reported as decoded, not confirmed against Clarion documentation.
- Sample bytes (plaintext or ciphertext) were not committed anywhere; only decoded
  facts above, per the lab rule.

## Provenance

- Samples: sembiance.com/fileFormatSamples/document/clarionDatabase/ — DEFAULT.DAT,
  GENESOFT.DAT, GEORGEA.DAT, GEORGEE.DAT, GEORGEX.DAT, HHCNTRL.DAT (+ plain
  BBRAND/CRDTCARD/HHNAMES/TAPE for calibration), fetched 2026-11-12 to /tmp; sizes
  byte-identical to F-38's census.
- Prior art: F-38's `docs/clarion-dat-format.md` (layout, identities, first 2 keys,
  per-section phase-reset hypothesis), clarionlife.net layout article (via F-38).
- Attack tooling: throwaway stdlib-Python brute-forcer/decoder in /tmp (not
  committed; the JSON records the method).
