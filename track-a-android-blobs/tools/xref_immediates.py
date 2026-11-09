#!/usr/bin/env python3
"""xref_immediates.py — match ath11k protocol constants in DECODED firmware
instructions (immediate operands only — much less noisy than raw byte scans).

Decodes wpss.b07's code with capstone (RV32+RVC), extracts immediate operands,
reports occurrences of ath11k HTC service/message IDs with the surrounding
disassembly context.

Usage: python3 xref_immediates.py <wpss.b07> [code_offset]
"""
import sys
from capstone import Cs, CS_ARCH_RISCV, CS_MODE_RISCV32, CS_MODE_RISCVC

HTC_MSGS = {1: "HTC_MSG_READY", 2: "HTC_MSG_CONNECT_SERVICE",
            3: "HTC_MSG_CONNECT_SERVICE_RESP", 4: "HTC_MSG_SETUP_COMPLETE"}

SVC_IDS = {}
for gname, g in (("WMI", 1), ("NMI", 2), ("HTT", 3), ("CFG", 4),
                 ("IPA", 5), ("PKTLOG", 6), ("TEST", 254)):
    for idx in range(0, 7):
        SVC_IDS[(g << 8) | idx] = f"SVC_{gname}.{idx}"


def parse_imms(op_str):
    """Extract numeric immediates from a capstone RISC-V op_str."""
    imms = []
    for tok in op_str.replace(",", " ").split():
        tok = tok.strip()
        try:
            v = int(tok, 0)
            imms.append(v)
        except ValueError:
            continue
    return imms


def main():
    path = sys.argv[1]
    code_off = int(sys.argv[2]) if len(sys.argv) > 2 else 16384
    data = open(path, "rb").read()[code_off:]
    md = Cs(CS_ARCH_RISCV, CS_MODE_RISCV32 | CS_MODE_RISCVC)
    insns = list(md.disasm(data, 0x404000))
    print(f"decoded {len(insns)} instructions from {path.split('/')[-1]} @+{code_off}")

    hits = {}  # value -> list of (addr, mnemonic, op_str)
    for insn in insns:
        for v in parse_imms(insn.op_str):
            if v in HTC_MSGS or v in SVC_IDS:
                hits.setdefault(v, []).append((insn.address, insn.mnemonic, insn.op_str))

    if not hits:
        print("NO ath11k protocol constants found in immediate operands — "
              "documented negative result (constants may be in literal pools, "
              "constructed at runtime, or use a different HTC dialect).")
        return
    print("\nmatches (immediate operands):")
    for v, lst in sorted(hits.items(), key=lambda kv: -len(kv[1])):
        label = HTC_MSGS.get(v) or SVC_IDS.get(v)
        print(f"\n  {label} (0x{v:x}) — {len(lst)} hits")
        for addr, mn, ops in lst[:5]:
            print(f"    {addr:08x}: {mn} {ops}")


if __name__ == "__main__":
    main()
