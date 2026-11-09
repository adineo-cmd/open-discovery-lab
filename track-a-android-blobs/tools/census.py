#!/usr/bin/env python3
"""census.py — full census of proprietary files in an extracted Android image tree.

Records only DERIVED FACTS (paths, sizes, hashes, file-type identifications,
ELF metadata). Never emits binary content. Safe to commit: see repo principle 1.

Usage:
  python3 census.py <extracted-image-root> [--out census.json] [--md census.md]
"""
import argparse
import hashlib
import json
import os
import struct
import sys
from collections import Counter, defaultdict

# Well-known magic signatures relevant to Android firmware
MAGICS = [
    (b"\x7fELF", "ELF"),
    (b"pIL\r", "QUALCOMM-MDT-HEADER"),  # 'p','I','L','\r' — PIL/MDT split image header
    (b"BAREBOX", "BAREBOX"),
    (b"ANDR", "ANDROID-BOOT"),
    (b"AVB0", "AVB-FOOTER/HEADER"),
    (b"CrAU", "OTA-PAYLOAD"),
    (b"QCDT", "QCDT"),
    (b"BOOTLDR", "BOOTLDR"),
    (b"\xd0\xcd\xd5\xa6", "QC-SWID"),  # common Qualcomm signed-header magic
    (b"SBL1", "SBL1-PROBABLE"),
    (b"PK\x03\x04", "ZIP"),
    (b"\x1f\x8b", "GZIP"),
    (b"BZh", "BZIP2"),
    (b"\xfd7zXZ", "XZ"),
    (b"ustar", "TAR"),
    (b"DHC", "DHC"),  # QC device histogram / misc
    (b"APTJ", "QC-APTJ"),  # QC partition table variant
    (b"QC\x00\x00", "QC-BIN-PROBABLE"),
]

# Qualcomm Hexagon / architectures of interest (ELF e_machine values)
EM_NAMES = {
    2: "SPARC", 3: "x86", 8: "MIPS", 20: "PowerPC", 40: "ARM",
    42: "SuperH", 50: "IA-64", 62: "x86-64", 83: "AVR",
    87: "V850", 88: "M32R", 92: "Altera Nios II", 93: "TI PRU",
    94: "RISC-V (old, bespoke)", 183: "AArch64", 164: "QDSP6 / Hexagon",
    243: "RISC-V", 247: "BPF", 252: "C-SKY", 242: "LoongArch",
    189: "MicroBlaze", 110: "DLX", 113: "NIOS", 166: "Xtensa",
    190: "ARC", 195: "TILE64", 216: "Kalimba (CSR)", 199: "RISC-V (historic 0xC7)",
}

PF_NAMES = {1: "X", 2: "W", 4: "R"}

PT_NAMES = {
    0: "NULL", 1: "LOAD", 2: "DYNAMIC", 3: "INTERP", 4: "NOTE",
    6: "PHDR", 7: "TLS",
    0x60000000: "LOOS", 0x6474e550: "GNU_EH_FRAME", 0x6474e551: "GNU_STACK",
    0x6474e552: "GNU_RELRO", 0x6474e553: "GNU_PROPERTY",
    0x70000000: "LOPROC", 0x70000001: "ARM_EXIDX",
    0x70000002: "QCOM_QSEE_PROBABLE", 0x68000000: "HIOS",
}


def sniff_magic(head: bytes):
    for magic, name in MAGICS:
        if head.startswith(magic):
            return name
    return None


def classify_family(relpath: str) -> str:
    p = relpath.lower()
    if "qca6750" in p or "wlan" in p or "wcnss" in p or "wpss" in p:
        return "wifi-wpss"
    if "bluetooth" in p or "btnv" in p or "btfm" in p or "/bt/" in p:
        return "bluetooth"
    if "/modem/" in p or "non-hlos" in p or "mpss" in p or "mba.mbn" in p or "q6" in p:
        return "modem-qdsp6"
    if "adsp" in p or "cdsp" in p or "sdsp" in p or "modemr" in p:
        return "dsp-firmware"
    if "tz" in os.path.basename(p) or "keymaster" in p or "gatekeeper" in p or "tee" in p:
        return "trustzone"
    if "fingerprint" in p or "goodix" in p or "fpc" in p or "focaltech" in p:
        return "input-fingerprint-touch"
    if "touch" in p:
        return "touchscreen"
    if "sns" in p or "sensor" in p or "slpi" in p:
        return "sensors"
    if "widevine" in p or "drm" in p or "hdcp" in p:
        return "drm"
    if "mcfg" in p or "qmi" in p:
        return "modem-config"
    if "venus" in p or "video" in p:
        return "video-firmware"
    if "camx" in p or "camera" in p or "chi" in p:
        return "camera"
    return "other"


def parse_elf(path: str, max_phdrs: int = 32):
    """Parse ELF header + program headers with stdlib only (no pyelftools dep)."""
    info = {"is_elf": False}
    try:
        size = os.path.getsize(path)
        if size < 64:
            return info
        with open(path, "rb") as f:
            head = f.read(64)
            if not head.startswith(b"\x7fELF"):
                return info
            info["is_elf"] = True
            ei_class, ei_data = head[4], head[5]
            info["class"] = {1: "ELF32", 2: "ELF64"}.get(ei_class, f"unk{ei_class}")
            info["endian"] = {1: "LE", 2: "BE"}.get(ei_data, f"unk{ei_data}")
            fmt = "<" if ei_data == 1 else ">"
            if ei_class == 1:  # ELF32
                (e_type, e_machine) = struct.unpack_from(fmt + "HH", head, 16)
                e_entry, e_phoff = struct.unpack_from(fmt + "II", head, 24)
                e_phentsize, e_phnum = struct.unpack_from(fmt + "HH", head, 42)
            else:  # ELF64
                (e_type, e_machine) = struct.unpack_from(fmt + "HH", head, 16)
                (e_entry, e_phoff) = struct.unpack_from(fmt + "QQ", head, 24)
                e_phentsize, e_phnum = struct.unpack_from(fmt + "HH", head, 54)
            info["type"] = {1: "REL", 2: "EXEC", 3: "DYN", 4: "CORE"}.get(e_type, e_type)
            info["machine_id"] = e_machine
            info["machine"] = EM_NAMES.get(e_machine, f"UNKNOWN({e_machine})")
            info["entry"] = e_entry
            info["phnum"] = e_phnum
            if e_phoff and 0 < e_phentsize and e_phnum:
                with open(path, "rb") as g:
                    g.seek(e_phoff)
                    phdrs = []
                    n = min(e_phnum, max_phdrs)
                    for i in range(n):
                        if ei_class == 1:
                            raw = g.read(32)
                            if len(raw) < 32:
                                break
                            p_type, p_offset, p_vaddr, _p_paddr, p_filesz, _p_memsz, p_flags, _p_align = \
                                struct.unpack(fmt + "IIIIIIII", raw)
                        else:
                            raw = g.read(56)
                            if len(raw) < 56:
                                break
                            p_type, p_flags, p_offset, p_vaddr, _p_paddr, p_filesz, _p_memsz, _p_align = \
                                struct.unpack(fmt + "IIQQQQQQ", raw)
                        phdrs.append({
                            "type": PT_NAMES.get(p_type, hex(p_type)),
                            "flags": "".join(PF_NAMES.get(b, "?") for b in (1, 2, 4) if p_flags & b),
                            "offset": p_offset, "vaddr": p_vaddr, "filesz": p_filesz,
                        })
                    info["phdrs"] = phdrs
                    if e_phnum > max_phdrs:
                        info["phdrs_truncated"] = e_phnum - max_phdrs
    except (OSError, struct.error) as e:
        info["error"] = str(e)
    return info


def census(root: str):
    rows = []
    per_family_files = Counter()
    per_family_bytes = Counter()
    machines = Counter()
    for dirpath, _dirnames, filenames in os.walk(root):
        for fn in filenames:
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, root)
            try:
                st = os.stat(full)
                size = st.st_size
                with open(full, "rb") as f:
                    head = f.read(256)
                sha = hashlib.sha256()
                with open(full, "rb") as f:
                    for chunk in iter(lambda: f.read(1 << 20), b""):
                        sha.update(chunk)
                fam = classify_family(rel.replace(os.sep, "/"))
                magic_name = sniff_magic(head)
                elf = parse_elf(full)
                row = {
                    "path": rel, "size": size, "sha256": sha.hexdigest(),
                    "family": fam, "magic": magic_name, "elf": elf,
                }
                rows.append(row)
                per_family_files[fam] += 1
                per_family_bytes[fam] += size
                if elf.get("is_elf"):
                    machines[elf.get("machine", "?")] += 1
            except OSError as e:
                rows.append({"path": rel, "error": str(e)})
    return rows, per_family_files, per_family_bytes, machines


def write_md(out_path, rows, per_family_files, per_family_bytes, machines, root):
    total = sum(per_family_files.values())
    with open(out_path, "w") as f:
        f.write("# Blob census — derived facts only\n\n")
        f.write(f"Root: `{root}` · files: {total} · "
                f"total bytes: {sum(per_family_bytes.values()):,}\n\n")
        f.write("## ELF machine architectures observed\n\n")
        f.write("| machine | count |\n|---|---|\n")
        for m, c in machines.most_common():
            f.write(f"| {m} | {c} |\n")
        f.write("\n## Families\n\n| family | files | bytes |\n|---|---|---|\n")
        for fam in sorted(per_family_files, key=lambda x: -per_family_bytes[x]):
            f.write(f"| {fam} | {per_family_files[fam]} | {per_family_bytes[fam]:,} |\n")
        f.write("\n## All files (hash, type, ELF machine)\n\n")
        f.write("| path | size | magic | ELF machine | sha256 (16) |\n|---|---|---|---|---|\n")
        for r in sorted(rows, key=lambda r: r.get("path", "")):
            if "error" in r:
                continue
            elf = r.get("elf", {})
            f.write(f"| `{r['path']}` | {r['size']:,} | {r.get('magic') or '-'} | "
                    f"{elf.get('machine', '-') if elf.get('is_elf') else '-'} | "
                    f"`{r['sha256'][:16]}` |\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--out", default="census.json")
    ap.add_argument("--md", default="census.md")
    args = ap.parse_args()
    rows, pf, pb, machines = census(args.root)
    with open(args.out, "w") as f:
        json.dump({"root": args.root, "rows": rows,
                   "per_family_files": dict(pf), "per_family_bytes": dict(pb),
                   "machines": dict(machines)}, f, indent=1)
    write_md(args.md, rows, pf, pb, machines, args.root)
    print(f"census: {sum(pf.values())} files → {args.out}, {args.md}")


if __name__ == "__main__":
    main()
