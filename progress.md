# Progress

## Completed
- 2026-11-09: lab kickoff; FP6 census (F-5..F-7); grid Ramsey row 9 (F-10)
- 2026-11-11: QURT (F-8), WMI xref (F-9), Gaia harvest (F-11), MD32 identification (F-36)
- 2026-11-12: blink vetting (F-13/21), Hexagon unlock (F-28), 3-color math (F-24/27/30), BT/TZ census (F-14), boot chain (F-15), EVROS=WCN6450 (F-32), LPEC packet layer (F-47)
- 2026-11-13: format-RE activation (F-34), campaign note, MD32 gap (F-45), ledger syncs

## Metrics
- Ledger: F-1..F-49 (49 verified findings)
- Formats decoded/cracked: PVD, IGS text layer, PD container, Clarion 6/6 encryption, DWM envelope+header, LPEC packet+frame layers
- OEIS-relevant: T(9,3..6) exact, a(9) bounds, 3-color frontier values, T_3(13,7)=2 exact

## Next steps
- EXEPACK unpack → DWM opcodes (running)
- LPEC pass 4: pulse allocator mirror (FUN_10003d80/10004450) → intra-frame pulse split
- LPEC pass 5: codebook wiring (excitation pages, LSP expansion, synthesis) → PCM output
- OEIS filing (owner account)
- Codeberg PRs (owner login)

## 2026-11-14 (LPEC pass 3 session)
- LPEC LP bit layout RESOLVED from code (FUN_10005040/05bf0/05ca0/05d50/060e0/04450/03e60); per-type bit targets 384/288/480/384 (LP) and 1024/768/1280/1024 (SP) == CUnitter nibble tables; 2-bit frame type is the mode nibble source.
- lpec_decoder.py: continuous-stream parser closes audio byte-exact on both LPEC samples — budgtele 50545 frames / 2426196 B / 6000.1 bps, MSV 159 frames / 20352 B / 16000.0 bps, zero invalid; tail-pad signature {3,9,17} matches derived formula; MSV 16k frame size resolved (128 B type-0); per-packet reset + 6-B trailer refuted.
- Pushed commits 2b394a19 (docs/lpec-decode-pass3.md + lpec_decoder.py) and fd51ec2c (lpec-decode-pass3.json) to adineo-cmd/open-discovery-lab main.
- Not yet: PCM synthesis (pulse split + codebook wiring) — honest negatives in the doc.

## 2026-11-14 (ledger sync session, ~13:40 local)
- Pushed FINDINGS.md (65 lines, 72,035 B, sha256 662a4403e5bd6b6457be87bbb5142641e818312667c5199c63e57870941ad824) to adineo-cmd/open-discovery-lab main as commit 9b74f5a27bad78075f7f2e4fe961ce80530807f5 ("Ledger sync: F-46..F-54 rows (DWM grammar FULL, LPEC decode passes 2-3, format-RE campaign, NTitler crack)").
- Race note: another sync agent had already landed F-46..F-53 (commit b9be63c2, 09:37:55Z) and the identical F-54 row (commit 3d6fb76b) between this session's fetch and push — so commit 9b74f5a2 is a zero-diff duplicate on top; linear history preserved, nothing orphaned, no force-push.
- Verification: fetch-back from raw.githubusercontent at 9b74f5a2 is byte-identical (cmp) and sha256-matches local; git blob f55b5ba98cc5175671eba8c340ba2b44688519db matches.
- Remote-only content check: none — diff of pre-push remote (b9be63c2) vs local showed exactly one added line (F-54); header paragraphs identical.
