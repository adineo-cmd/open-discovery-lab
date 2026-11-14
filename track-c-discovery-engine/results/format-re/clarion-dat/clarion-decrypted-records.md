# Clarion .DAT record bodies — decrypted (F-47)

**Claim:** the first full decryption of the record bodies of the six encrypted Clarion .DAT samples in the sembiance `clarionDatabase` corpus (and, to our knowledge, the first published decryption of Clarion 2.x .DAT record bodies generally). Using the per-file 2-byte XOR keys cracked in F-39 with the body-phase model, all six files yield complete, readable, cross-consistent 1989–1992 business data: a 1991 family journal (12 entries fully reassembled), a shareware password table, a home-health control record with real phone numbers, and a timeclock defaults record. Bodies validate against the F-38 schema on every check, and the DECIMAL interpretation from F-38/F-39 is corrected (leading pad nibble, not trailing).

- Date: 2026-11-14 · Agent: F-47 · Track: track-c-discovery-engine
- Samples re-fetched from `sembiance.com/fileFormatSamples/document/clarionDatabase/` to /tmp only; sizes match the F-38 census and F-39 metadata exactly (DEFAULT 3037, GENESOFT 595, GEORGEA 365, GEORGEE 1545, GEORGEX 3123, HHCNTRL 928).
- Keys from `clarion-encryption-keys.json` (F-39): DEFAULT `d8c6`, GENESOFT `d3c6`, GEORGEA `3e3a`, GEORGEE `3e3a`, GEORGEX `3e3a`, HHCNTRL `5056`.
- Machine-readable companion: `clarion-decrypted-records.json` (all field descriptors, all records, raw BCD nibbles, validation evidence).

## Method (confirmed by successful body decryption)

Per file, 2-byte periodic XOR: plaintext = cipher XOR k0 at even keystream index, k1 at odd. Keystream phase resets at each section start (header body @0x04, each 27-byte field descriptor, each 19-B KEYSECT / 6-B KEYPART, picture/array sections). Record slots: the 5-byte rhd/rptr header is stored CLEAR and only the body is encrypted, with the keystream reset to k0 at body byte 0 — exactly the F-39 model, now proven at the record level:

1. With this model, all 6 encrypted files satisfy the F-38 header arithmetic (`desc_end == offset`, `filesize == offset + numrecs*reclen`) — 6/6, same as the 43 plain files.
2. Slot bytes 0–4 read CLEAR give rhd ∈ {0x01, 0x05} active / {0x11, 0x15} deleted, and the GEORGEE freelist chain reproduces exactly: `freerec 6 → 28 → 27 → 26 → 25 → 1 → 23 → 22 → 21 → 20 → 19 → 18 → 17 → 16 → 14 → 13 → 12` (17 deleted slots == header numdels 17, ends rptr 0).
3. GEORGEX records whose 68-char TEXT field is completely full end in letters (`d`, `y`, `w`): the final body byte IS encrypted (raw 0x5e/0x43/0x4d = letter XOR k1 0x3a).
4. HHCNTRL's final body byte decrypts to 0x70 = `'p'` (HHC:REGISTERED); GEORGEA's empty-password field decrypts to 12 spaces.
5. Control: the inverted phase (k1 first) yields garbage; decrypting the whole slot including the "header" (as the repo decoder's `records()` still does) would corrupt the clear rhd/rptr bytes. Note `clarion_dat_decode.py::records()` should be updated to the body-reset model.

## Validation summary

| Check | Result |
|---|---|
| Header arithmetic (desc_end==offset, size==offset+numrecs*reclen) | 6/6 encrypted + 3/3 plain re-fetched samples |
| STRING fields printable ASCII | all, across all files (except documented anomalies below) |
| GEORGEE NTR:DATE (LONG) valid calendar dates | 29/29 (1991-01-01 … 1991-05-19) |
| GEORGEE NTR:TIME (LONG) valid times | 29/29 (07:39:xx … 22:26:xx, all 1991-plausible) |
| DEFAULT time LONGs | 15/15 first-pattern fields = 08:00:00.00 in / 12:00:00.00 lunch / 17:00:00.00 out; patterns 2–3 stored as 0 |
| Deleted-slot marker (rhd bit 0x10) on decrypted bodies | GEORGEE 17 (== numdels), HHNAMES 5; freelist chain intact |
| GEORGEX → GEORGEE referential integrity | NTRYREC ∈ {2,3,4,5,7,8,9,10,11,15,24,29} = exactly the 12 active GEORGEE slots (+ one 0-ref); TEXTNUM contiguous 1..n per entry |
| Agreement with F-39's published values | matches on every field except where noted below |

**Deleted-slot forensics (refutes the working expectation):** GEORGEE's 17 deleted slots are NOT empty/password-cleared — all retain fully readable, correctly decrypted bodies (titles, dates, times intact). Deletion is a soft delete: set rhd bit 0x10 and link the slot into the freelist via rptr; the body is never wiped. Same for HHNAMES's 5 deleted slots (including the author's own test records). Deleted records are recoverable as-is.

## DECIMAL format correction (affects F-38 schema)

F-38/F-39 read DECIMAL by dropping the LAST nibble. The data shows the pad nibble is LEADING: stored nibbles = [pad if total digits odd] + integer digits (decsig) + fraction digits (decdec). No sign nibble observed in these samples (all unsigned).

| Field | stored nibbles | corrected reading | F-38 reading |
|---|---|---|---|
| TAXRATE NJ TAX:RATE (decsig 3, decdec 4) | `00000700` | digits `0000700` → **0.0700 = 7% NJ sales tax** | 0.0070 |
| HHNAMES slot1 HHN:PHONE_NO | `0000008044885506` | **(804) 488-5506** — matches the record's own address "Chesapeake, VA 23321" | 9-digit `804488550` (invalid) |
| HHCNTRL HHC:POLICE / FIRE / AMBULANCE | `0000000000000911` | **911** (×3, US emergency number) | `091` |
| HHCNTRL HHC:DOCTOR | `0000000004542323` | **4542323** (7-digit local number) | 454232 |
| HHCNTRL OTHERPHONE1 / 2 | `0000000004345678` / `0000000005456787` | 4345678 / 5456787 | 434567 / 545678 |

## Recovered data per file

### GEORGEA.DAT — author/registration record (key 3e3a, 1 record, 1991-05-24)

| Field | Value |
|---|---|
| ATH:AUTHOR | George Tanner |
| ATH:ADDRESS1 | 123 Main Street |
| ATH:ADDRESS2 | Anywhere, USA |
| ATH:TITLE | GEORGE'S JOURNAL |
| ATH:PASSWORD | *(empty — 12 spaces; no password set)* |

### GEORGEE.DAT — journal entry index (key 3e3a, 29 slots / 17 deleted)

| slot | rhd | del | rptr | date | time | NTR:NAME |
|---|---|---|---|---|---|---|
| 1 | 0x11 | yes | 23 | 1991-02-15 | 07:48:57.83 | AMY, THE STAR |
| 2 | 0x01 | | 0 | 1991-01-01 | 07:39:23.20 | NEW YEAR'S DAY |
| 3 | 0x05 | | 0 | 1991-01-10 | 07:39:40.01 | REPORT CARDS |
| 4 | 0x05 | | 0 | 1991-01-12 | 07:39:51.21 | RIDE IN THE VAN |
| 5 | 0x05 | | 0 | 1991-02-01 | 07:40:02.03 | A NEW MONTH |
| 6 | 0x11 | yes | 28 | 1991-05-19 | 20:51:17.82 | CHURCH TODAY |
| 7 | 0x01 | | 0 | 1991-05-18 | 21:01:34.96 | CAMPING TRIP |
| 8 | 0x01 | | 0 | 1991-01-02 | 22:18:13.93 | BACK TO WORK |
| 9 | 0x01 | | 0 | 1991-01-04 | 22:19:24.94 | NORMAL DAY |
| 10 | 0x01 | | 0 | 1991-01-06 | 22:19:40.05 | CHURCH |
| 11 | 0x01 | | 0 | 1991-01-08 | 22:20:21.68 | NORMAL DAY |
| 12 | 0x15 | yes | 0 | 1991-01-14 | 22:20:29.21 | NORMAL DAY |
| 13 | 0x11 | yes | 12 | 1991-01-15 | 22:21:47.64 | NORMAL DAY |
| 14 | 0x11 | yes | 13 | 1991-01-18 | 22:21:59.72 | ANOTHER NORMAL DAY |
| 15 | 0x05 | | 0 | 1991-01-19 | 22:22:10.05 | ACTIVITY DAY |
| 16 | 0x11 | yes | 14 | 1991-01-26 | 22:22:41.25 | MOW THE LAWN DAY |
| 17 | 0x11 | yes | 16 | 1991-01-27 | 22:22:51.63 | CHURCH DAY |
| 18 | 0x11 | yes | 17 | 1991-01-29 | 22:23:05.74 | MONTH'S ALMOST OVER |
| 19 | 0x11 | yes | 18 | 1991-02-02 | 22:23:33.87 | ACTIVITY DAY |
| 20 | 0x11 | yes | 19 | 1991-02-04 | 22:23:50.07 | CHILDREN'S SCHOOL WORK |
| 21 | 0x11 | yes | 20 | 1991-02-06 | 22:24:02.21 | TED'S PROBLEMS |
| 22 | 0x11 | yes | 21 | 1991-02-08 | 22:24:14.18 | AMY LEARNS A LESSON |
| 23 | 0x15 | yes | 22 | 1991-02-10 | 22:24:19.62 | WHAT A DAY! |
| 24 | 0x05 | | 0 | 1991-02-18 | 22:25:01.75 | AMY, THE STAR! |
| 25 | 0x11 | yes | 1 | 1991-02-19 | 22:25:23.83 | NORMAL DAY |
| 26 | 0x11 | yes | 25 | 1991-02-22 | 22:25:33.93 | NORMAL DAY |
| 27 | 0x11 | yes | 26 | 1991-02-24 | 22:25:44.48 | NORMAL DAY |
| 28 | 0x11 | yes | 27 | 1991-03-01 | 22:26:02.71 | THE BEGINNING OF MARCH |
| 29 | 0x01 | | 0 | 1991-03-21 | 22:26:12.71 | SPRING BEGINS |

### GEORGEX.DAT — journal text (key 3e3a, 38 slots, 0 deleted)

38 lines of TXT:NTRYREC / TXT:TEXTNUM / TXT:TEXT (68-char wrapped lines) join 1:1 into the GEORGEE entries; the full line table is in the JSON. **New format finding:** the journal app writes a plaintext **0xFF end-of-text sentinel** immediately after the last content byte of an entry's final line (15/38 records carry it: the final line of each of the 12 entries plus the emptied slot 23, which contains a lone 0xFF and no text). F-39's published texts silently dropped this byte; raw bytes at sentinel positions alternate 0xC1/0xC5 = plaintext 0xFF XOR k(3e3a), so it is genuine body content.

**Reassembled journal of George Tanner, 1991** (12 recovered entries; titles/dates from GEORGEE, lines from GEORGEX in TEXTNUM order, 0xFF stripped):

> **1991-01-01 — NEW YEAR'S DAY** · "Today is New Year's Day. I'm home with the family. My wife and I and the kids all stayed up to welcome in the New Year. We stayed home and played games last night. This morning we were all so tired that we never woke up until 11 o'clock. My wife went out for a bit of shopping while the kids and I watched TV."
>
> **1991-01-10 — REPORT CARDS** · "The kids all brought home their report cards today. Billy got straight A's. He is doing real well. Julie has been attending a special art class which she enjoys. She only got one B, the rest A's. Good kids!"
>
> **1991-01-12 — RIDE IN THE VAN** · "It was a quiet day today. We went for a ride in the van to see the countryside."
>
> **1991-02-01 — A NEW MONTH** · "February has begun. The kids went to the mountains last weekend to go tubing. They had a fun time. I wish I had been able to go, but had some other things to do."
>
> **1991-05-18 — CAMPING TRIP** · "We went on a camping trip on Friday night. I always have a hard time sleeping on the ground. I told the kids some scary stories and they kept me up to late. The next morning we went for a hike. We found a nice tarzan-swing type vine that we played on for hours."
>
> **1991-01-02 — BACK TO WORK** · "I went back to work today after a long four day weekend vacation. The holidays are over. No New Year resolutions for me."
>
> **1991-01-04 — NORMAL DAY** · "Just another normal day at the office. It's hard to want to get back to work after the holidays."
>
> **1991-01-06 — CHURCH** · "The family went to church today. There was a boring sermon as usual."
>
> **1991-01-08 — NORMAL DAY** · "Another normal day. The kids are all doing well in school. Report cards come out in two days. I think they should all have good grades."
>
> **1991-01-19 — ACTIVITY DAY** · "We had an activity day today at the school. All of the children ran races and got some ribbons. We had a fun time."
>
> **1991-02-18 — AMY, THE STAR!** · "This evening Amy had a piano recital. Her teacher said she did very well and we were all pleased. The whole family attended and we enjoyed Amy's performance."
>
> **1991-03-21 — SPRING BEGINS** · "The trees are budding and spring is coming. I had to work on my lawn mower to get it ready. The spring rains will make the lawn grow like a jungle."

### GENESOFT.DAT — password/answer table (key d3c6, 1 record, 1989-08-28 — oldest file)

12 STRING fields with obfuscated names (GEN: prefix); decoded values are lowercase jumbles — an answer-key table for shareware copy protection:

| Field | Value |
|---|---|
| GEN:SOIFXCFRJ | ooqwxsqde |
| GEN:OWLDMESQX | asmnjuwrt |
| GEN:PASSWORDS | psdjxczny |
| GEN:HIURTSRSP | shkj |
| GEN:PASQOEXZR | wrclk |
| GEN:SLKEEIXXA | weuyhbnvc |
| GEN:IPYHWSQIP | fgvbnmxzs |
| GEN:DKAPMBHSL | **shareware** |
| GEN:YHIKLZCBA | djkmnbvcw |
| GEN:SWERCFJKL | woikmj |
| GEN:POEXDSLSG | yuhjlxcva |
| GEN:WEXDJNBMK | qawsedrft |

("shareware" is the only readable word; qawsedrft is a keyboard-pattern string. See anomalies for the stray final byte.)

### HHCNTRL.DAT — HomeHealth control record (key 5056, 1 record, 1990-07-24, Torbert Data Systems)

| Field | Value |
|---|---|
| HHC:SERIAL_NO | S10000004 |
| HHC:HH_NO | 1 |
| HHC:NOTICE | "  Copyright 1990 Torbert Data Systems, INC." |
| HHC:PWORD / HHC:POLICE | "Police" / **911** |
| HHC:FWORD / HHC:FIRE | "Fire" / **911** |
| HHC:AWORD / HHC:AMBULANCE | "Ambulance" / **911** |
| HHC:DWORD / HHC:DOCTOR | "Doctor" / **4542323** |
| HHC:PEWORD / HHC:PEDIATRICIAN | "Pediatrician" / 0 |
| HHC:POWORD / HHC:POISON | "Poison" / 0 |
| HHC:OTHERNAME1 / OTHERPHONE1 | "Power Company" / **4345678** |
| HHC:OTHERNAME2 / OTHERPHONE2 | "Gas Company" / **5456787** |
| HHC:OTHERNAME3 / OTHERPHONE3 | "" / 0 |
| HHC:REGISTERED | "p" |

### DEFAULT.DAT — timeclock defaults (key d8c6, 1 record, 98 fields, 1991-05-05)

DEF:OVERRIDE=Y, DEF:WINDOW=5.0, DEF:LUNCH=60.0, DEF:DEDUCT=N, DEF:STATE="", DEF:AREA=000, DEF:PWDEXIT=Y, DEF:MAXHOUR=7.0. Pattern 1 (MON–FRI): IN 08:00:00.00, LUNCH 12:00:00.00, OUT 17:00:00.00 (LONG times 2880001/4320001/6120001); patterns 2–3 all empty/zero. All 98 values in the JSON (one caveat below).

## Honest negatives / anomalies

1. **Final-byte deviation in DEFAULT.DAT and GENESOFT.DAT (1 byte each).** 300/301 (resp. 180/181) body bytes decrypt consistently; the last file byte (raw 0x00 / 0x20) decrypts to 0xd8 / 0xf3 under the model. Consequence: DEFAULT DEF:WD5OUTIME3 reads −671088640 under the strict model (F-39 published 0, i.e. treated that byte as clear), and GENESOFT GEN:WEXDJNBMK carries a stray 0xf3 after "qawsedrft" + padding. Pattern note: both anomalous files share k1=0xc6; the four clean files (3e3a×3, 5056) encrypt their final byte consistently. Interpretation open — per-driver-version trailing-byte handling (GENESOFT is the 1989 file) or a clear EOF/flush byte. No other byte deviates in any file.
2. **Signed DECIMAL unobserved.** All DECIMAL fields in these samples are unsigned; the sign-nibble rule (if any) remains unverified.
3. **Even-digit-count DECIMALs unobserved.** Every DECIMAL here has an odd digit total (leading pad nibble); the even case needs no pad by the model but has no direct sample.
4. **GENESOFT password semantics not recoverable** from this file alone: the values are opaque jumbles (one readable word, "shareware"); the app's scrambling of the user's typed answer (if any) is not in the .DAT.
5. Deleted-slot bodies were expected (in the task brief) to be empty/password-cleared — the data refutes this; they retain full plaintext.

## Plain-sample cross-reference (no key; same schema)

- **HHNAMES.DAT** (HomeHealth, same app as HHCNTRL): 7 slots / 5 deleted — deleted retain full data (W. V. Torbert 3916 Plum Lane Chesapeake VA 23321 (804) 488-5506; a "1234567890…" dummy test record; R. E. Smith "Baltamore, MD" [sic] 809-444-6712). Active: Cathy M Sample (Houston TX), John H Doe (Virginia Beach VA, 804-123-4567). Phone numbers validate the leading-pad DECIMAL reading (8044885506 = valid 10-digit number with area code matching the address's state).
- **TAXRATE.DAT**: NT/NON TAXABLE = 0.0000; NJ/NEW JERSEY = 0.0700 (7%) — validates the DECIMAL integer/fraction split (decsig 3, decdec 4).
- **APPOINTS.DAT**: 5 DAILY records with date LONGs (5/5 valid calendar dates) + array dimensions and a COMMENTS memo (memo file out of scope).

## Provenance

- Samples: sembiance.com/fileFormatSamples/document/clarionDatabase/ (fetched to /tmp only, 2026-11-14; sizes match F-38 census).
- Keys: F-39 (`clarion-encryption-keys.json`); schema: F-38 (`clarion-dat-format.md`); decoder: `clarion_dat_decode.py` (its `records()` whole-slot phase should be corrected to the body-reset model proven here).
- Raw sample bytes are not committed; every value above is a derived fact reproducible from the keys + this model.
