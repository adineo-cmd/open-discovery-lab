#!/usr/bin/env python3
"""wmi_b091012_scan.py — F-21: extend WMI dispatcher search to wpss.b09/.b10/.b12.

Same method as F-20 (wmi_dispatch_scan.py): RV32+C linear sweep with resync,
constant-propagation construction search, literal ID scan. These segment files
have no ELF headers on disk (raw payloads), so vaddr comes from wpss.mdt phdrs.
Also: tolerant .eh_frame chain parse for b09, strings pass for all three.
Usage: python3 -I wmi_b091012_scan.py <qca6750_dir> <mdt> <wmi.h> <out.json>

NOTE: the sys.path lines below are workspace-local (capstone lives in the
user site-packages; wmi_dispatch_scan.py and xref_wmi.py are lab-local).
Adjust for your environment.
"""
import json
import re
import struct
import sys
from collections import Counter

sys.path.insert(0, "/home/aditya/.local/lib/python3.12/site-packages")  # capstone (ignored by -I)
sys.path.insert(0, "/home/aditya/.zcode/workspace/draft-6b0eaffc-c308-4302-94d4-244a23b47158/scratch-wmi-dispatch")
from wmi_dispatch_scan import sweep, pattern_search, top_mnemonics  # F-20 method, reused verbatim

from capstone import Cs, CS_ARCH_RISCV, CS_MODE_RISCV32, CS_MODE_RISCVC

MARKERS = ["wmi", "WMI", "htc", "HTC", "endpoint", "ENDPOINT", "htt", "HTT",
           "qurt", "QURT", "task", "memheap", "wlan", "WLAN", "diag", "pmon"]


def parse_mdt(path):
    d = open(path, "rb").read()
    e_phoff = struct.unpack_from("<I", d, 28)[0]
    e_phentsize, e_phnum = struct.unpack_from("<HH", d, 42)
    e_machine = struct.unpack_from("<H", d, 18)[0]
    out = {"e_machine": e_machine, "phdrs": []}
    for i in range(e_phnum):
        o = e_phoff + i * e_phentsize
        t, off, va, pa, fsz, msz, fl, al = struct.unpack_from("<8I", d, o)
        out["phdrs"].append({"i": i, "type": t, "vaddr": va, "filesz": fsz,
                             "memsz": msz, "flags": fl})
    return out


def eh_frame_chain(data):
    """Tolerant u32-length chain parse: classify CIE (id==0) vs FDE."""
    off = 0
    n = len(data)
    cies = fdes = 0
    breaks = 0
    while off + 4 <= n:
        ln = struct.unpack_from("<I", data, off)[0]
        if ln == 0:
            break  # terminator
        if ln < 8 or off + 4 + ln > n:
            breaks += 1
            break
        cid = struct.unpack_from("<I", data, off + 4)[0]
        if cid == 0:
            cies += 1
        else:
            fdes += 1
        off += 4 + ln
    return {"end_off": off, "file_len": n, "chained_pct": round(100.0 * off / n, 1),
            "cies": cies, "fdes": fdes, "chain_breaks": breaks}


def scan_words_shape(data):
    """Words with grp<<12|1 shape; and exact 605-ID words."""
    shape = 0
    for a in range(0, len(data) - 3, 4):
        v = struct.unpack_from("<I", data, a)[0]
        if 0x1001 <= v <= 0xFF001 and (v & 0xFFF) == 1:
            shape += 1
    return shape


def scan_u16_ids(data, idvals):
    hits = {}
    for a in range(0, len(data) - 1, 2):
        v = struct.unpack_from("<H", data, a)[0]
        if v in idvals:
            hits.setdefault(v, []).append(a)
    return hits


def extract_strings(data, minlen=6):
    return re.findall(rb"[\x20-\x7e]{%d,}" % minlen, data)


def strings_pass(data):
    strs = extract_strings(data)
    joined = b"\n".join(strs)
    rep = {"n_strings": len(strs), "str_bytes": len(joined),
           "pct_of_file": round(100.0 * len(joined) / max(1, len(data)), 1),
           "markers": {}}
    for m in MARKERS:
        c = len(re.findall(re.escape(m.encode()), joined))
        if c:
            rep["markers"][m] = c
    # sample contexts for key markers
    samples = {}
    for m in ("wmi", "WMI", "htc", "HTC", "endpoint", "qurt", "QURT"):
        ms = [s.decode() for s in strs if m.encode() in s]
        if ms:
            samples[m] = ms[:8]
    rep["marker_samples"] = samples
    rep["first20"] = [s.decode(errors="replace")[:110] for s in strs[:20]]
    rep["longest10"] = sorted((s.decode(errors="replace")[:110] for s in strs), key=len)[-10:]
    return rep


def main():
    qdir, mdt_path, wmi_h, out_path = sys.argv[1:5]
    sys.path.insert(0, "/home/aditya/.zcode/workspace/draft-6b0eaffc-c308-4302-94d4-244a23b47158/open-discovery-lab/track-a-android-blobs/tools")
    import xref_wmi
    ids = xref_wmi.eval_wmi_h(open(wmi_h, encoding="utf-8", errors="replace").read())
    idvals = {v: k for k, v in ids.items() if isinstance(v, int) and 0x100 <= v <= 0xFFFF}

    mdt = parse_mdt(mdt_path)
    md = Cs(CS_ARCH_RISCV, CS_MODE_RISCV32 | CS_MODE_RISCVC)
    md.detail = False

    # file-size -> phdr mapping (unique on these sizes)
    segmap = {}
    for ph in mdt["phdrs"]:
        segmap.setdefault(ph["filesz"], []).append(ph)
    targets = {"b09": "wpss.b09", "b10": "wpss.b10", "b12": "wpss.b12"}

    report = {"mdt": {"e_machine": mdt["e_machine"], "note": "164=EM_QDSP6 (Hexagon); F-7 junk-field finding",
                      "phdrs": mdt["phdrs"]}, "segments": {}}

    for label, fname in targets.items():
        data = open(f"{qdir}/{fname}", "rb").read()
        rep = {"file": fname, "size": len(data),
               "elf_magic": data[:4] == b"\x7fELF",
               "first_bytes": data[:24].hex()}
        ph = segmap.get(len(data), [None])[0]
        if ph:
            rep["mdt_phdr"] = {"i": ph["i"], "type": ph["type"], "vaddr": hex(ph["vaddr"]),
                               "memsz": ph["memsz"], "flags": hex(ph["flags"]),
                               "flags_dec": "R" + ("W" if ph["flags"] & 2 else "") + ("X" if ph["flags"] & 1 else "")}
        vaddr = ph["vaddr"] if ph else 0
        # RV32+C sweep (whole file; honest even for data segments)
        insns = sweep(md, data, vaddr)
        decoded = sum(s for _a, s, _h, _m, _o in insns)
        rep["rv32_sweep"] = {"n_insns": len(insns), "decoded_bytes": decoded,
                             "coverage_pct": round(100.0 * decoded / max(1, len(data)), 1),
                             "mnemonic_top": top_mnemonics(insns, 10)}
        hits, slli12 = pattern_search(insns, vaddr)
        rep["construction_hits"] = hits
        rep["slli12_hits"] = slli12
        # data-table checks
        rep["word_grp12x1_shape_count"] = scan_words_shape(data)
        u16 = scan_u16_ids(data, idvals)
        rep["u16_id_hits"] = {hex(k): {"name": idvals[k], "count": len(v), "offs": [hex(x) for x in v[:6]]}
                              for k, v in sorted(u16.items())}
        w32 = {}
        for a in range(0, len(data) - 3, 4):
            v = struct.unpack_from("<I", data, a)[0]
            if v in idvals:
                w32.setdefault(v, []).append(a)
        rep["u32_id_hits"] = {hex(k): {"name": idvals[k], "count": len(v), "offs": [hex(x) for x in v[:6]]}
                              for k, v in sorted(w32.items())}
        if label == "b09":
            rep["eh_frame_chain"] = eh_frame_chain(data)
        rep["strings"] = strings_pass(data)
        report["segments"][label] = rep

    with open(out_path, "w") as f:
        json.dump(report, f, indent=1)

    for label, rep in report["segments"].items():
        ph = rep.get("mdt_phdr", {})
        print(f"== {label} ({rep['file']}, {rep['size']} B) elf={rep['elf_magic']} "
              f"phdr(type={ph.get('type')}, flags={ph.get('flags_dec')}, memsz={ph.get('memsz')})")
        sw = rep["rv32_sweep"]
        print(f"   RV32 sweep: {sw['n_insns']} insns, {sw['decoded_bytes']} B ({sw['coverage_pct']}%), "
              f"top: {sw['mnemonic_top'][:5]}")
        print(f"   construction: {len(rep['construction_hits'])}  slli12: {len(rep['slli12_hits'])}  "
              f"grp12x1-shape words: {rep['word_grp12x1_shape_count']}  "
              f"u16-ID vals: {len(rep['u16_id_hits'])}  u32-ID vals: {len(rep['u32_id_hits'])}")
        if "eh_frame_chain" in rep:
            print(f"   eh_frame chain: {rep['eh_frame_chain']}")
        st = rep["strings"]
        print(f"   strings: {st['n_strings']} ({st['pct_of_file']}% of file), markers: {st['markers']}")
        for m, ms in list(st["marker_samples"].items())[:3]:
            print(f"     [{m}] e.g. {ms[:2]}")


if __name__ == "__main__":
    main()
