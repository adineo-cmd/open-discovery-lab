#!/usr/bin/env python3
"""wpss_disasm.py — annotated RV32+RVC disassembly of wpss.b07 (WCN6750 wpss).

Produces the first public annotated disassembly of the WCN6750 wireless
processor firmware program segment. Facts only; no binary content committed.

Usage: python3 wpss_disasm.py <wpss.b07> [max_instr]
"""
import sys
from capstone import Cs, CS_ARCH_RISCV, CS_MODE_RISCV32, CS_MODE_RISCVC

CSR_NAMES = {
    0x300: "mstatus", 0x301: "misa", 0x304: "mie", 0x305: "mtvec",
    0x340: "mscratch", 0x341: "mepc", 0x342: "mcause", 0x343: "mtval",
    0x344: "mip", 0x7a0: "pmpcfg0", 0x7a1: "pmpcfg1", 0x7a2: "pmpcfg2",
    0x7b0: "pmpaddr0", 0x7b1: "pmpaddr1",
    0xc00: "cycle", 0xc01: "time", 0xc02: "instret",
    0xf11: "mvendorid", 0xf12: "marchid", 0xf13: "mimpid", 0xf14: "mhartid",
}


def annotate(insn):
    notes = []
    if insn.mnemonic in ("csrw", "csrs", "csrc", "csrr", "csrsi", "csrci", "cswi"):
        try:
            op = int(insn.op_str.split(",")[-1].strip(), 0)
            if op in CSR_NAMES:
                notes.append(f"; CSR: {CSR_NAMES[op]}")
        except ValueError:
            pass
    return " ".join(notes)


def main():
    path = sys.argv[1]
    max_n = int(sys.argv[2]) if len(sys.argv) > 2 else 400
    data = open(path, "rb").read()
    md = Cs(CS_ARCH_RISCV, CS_MODE_RISCV32 | CS_MODE_RISCVC)
    print(f"# Annotated disassembly of {path.split('/')[-1]} (entry segment, RV32+RVC)")
    print(f"# file offset 16384 (vaddr 0x404000), first {max_n} instructions\n")
    n = 0
    for insn in md.disasm(data[16384:], 0x404000):
        note = annotate(insn)
        print(f"{insn.address:08x}:  {insn.bytes.hex():<10} {insn.mnemonic:<10} {insn.op_str:<30} {note}")
        n += 1
        if n >= max_n:
            break
    print(f"\n# total decoded: {n}")


if __name__ == "__main__":
    main()
