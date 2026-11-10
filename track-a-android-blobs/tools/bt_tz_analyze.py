#!/usr/bin/env python3
"""bt_tz_analyze.py — census-level analysis of FP6 bluetooth + trustzone files.

Derived facts only: TLV/NVM header decode (against btqca.h structs), ELF
segment tables, version-string extraction, featenabler cross-check.
Usage: bt_tz_analyze.py <trees-tzbt-root> <census.json>
"""
import json
import os
import struct
import sys

ROOT = sys.argv[1]
CENSUS = sys.argv[2]
BT = os.path.join(ROOT, "bluetooth/image")
TZ = os.path.join(ROOT, "trustzone")
TEE = os.path.join(ROOT, "tee-apps")


def u16(b, o):
    return struct.unpack_from("<H", b, o)[0]


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def tlv_decode(path):
    """Decode a QCA TLV container per btqca.h struct layout.

    Empirical vendor layout (msbtfw11/12.tlv, evrbtfw20.tlv): 4-byte
    tlv_type_hdr, then 32 bytes of patch fields (8 bytes more than the
    upstream 24-byte struct tlv_type_patch), then the 4-byte entry at
    container offset 0x24, then patch code.
    """
    with open(path, "rb") as f:
        b = f.read()
    out = {"file": os.path.basename(path), "size": len(b)}
    type_len = u32(b, 0)
    out["type"] = type_len & 0xFF
    out["length_field"] = (type_len >> 8) & 0xFFFFFF
    out["file_minus_len"] = len(b) - out["length_field"]
    out["total_size"] = u32(b, 4)
    out["data_length"] = u32(b, 8)
    out["format_version"] = b[12]
    out["signature"] = b[13]
    out["download_mode"] = b[14]
    out["product_id"] = u16(b, 16)
    out["rom_build"] = u16(b, 18)
    out["patch_version"] = u16(b, 20)
    out["entry"] = u32(b, 36)  # at container offset 0x24
    rom_ver = ((out["rom_build"] & 0xF00) >> 4) | (out["rom_build"] & 0xF)
    out["rom_ver_per_kernel_math"] = rom_ver
    return out


def nvm_decode(path):
    """Walk NVM tags per btqca.c semantics (type 4 = enclosing header)."""
    with open(path, "rb") as f:
        b = f.read()
    out = {"file": os.path.basename(path), "size": len(b), "headers": [], "tags": []}
    off = 0
    while off + 4 <= len(b):
        tl = u32(b, off)
        typ = tl & 0xFF
        ln = (tl >> 8) & 0xFFFFFF
        out["headers"].append({"offset": off, "type": typ, "length": ln})
        if typ == 4:
            off += 4
            continue
        # inner: type-2 NVM tag set starts right after 4-byte header
        off += 4
        break
    # walk tags: tag_id u16, tag_len u16, reserve1 u32, reserve2 u32, data[tag_len]
    while off + 12 <= len(b):
        tag_id = u16(b, off)
        tag_len = u16(b, off + 2)
        if off + 12 + tag_len > len(b):
            out["tags"].append({"tag_id": tag_id, "tag_len": tag_len, "error": "overrun"})
            break
        data = b[off + 12:off + 12 + tag_len]
        out["tags"].append({
            "tag_id": tag_id, "tag_len": tag_len,
            "data_preview": data[:64].decode("ascii", "replace").rstrip("\x00"),
        })
        off += 12 + tag_len
    out["tail_unparsed"] = len(b) - off
    return out


def strings_version(path):
    """Version-string hunt (census-level; fact about the binary)."""
    import re
    with open(path, "rb") as f:
        data = f.read()
    pats = [
        rb"QC_IMAGE_VERSION_STRING[^\x00]*",
        rb"IMAGE_VERSION_STRING[^\x00]*",
        rb"OEM_IMAGE_VERSION_STRING[^\x00]*",
        rb"IMAGE_BUILD_ID_STRING[^\x00]*",
        rb"BTFW\.[A-Z]+\.[^\x00]{0,60}",
        rb"TZ\.[A-Z]+\.[^\x00]{0,60}",
        rb"HYP\.[A-Z]+\.[^\x00]{0,60}",
        rb"KEYMASTER[A-Z_.0-9]{0,60}",
        rb"DevCfg\.[^\x00]{0,60}",
        rb"UEFISECAPP[^\x00]{0,60}",
        rb"Keymaster[A-Za-z_.0-9 ]{0,60}",
    ]
    seen = []
    for pat in pats:
        for m in re.finditer(pat, data):
            s = m.group(0)[:120].decode("ascii", "replace")
            if s not in seen:
                seen.append(s)
    return seen


def print_phdrs(census, path_key):
    for r in census["rows"]:
        if r["path"] == path_key:
            e = r.get("elf", {})
            print(f"--- {path_key} size={r['size']} machine={e.get('machine')} "
                  f"type={e.get('type')} entry={hex(e.get('entry') or 0)} phnum={e.get('phnum')}")
            for ph in e.get("phdrs", []):
                print(f"    {ph['type']:>6} {ph['flags']:>4} off=0x{ph['offset']:x} "
                      f"vaddr=0x{ph['vaddr']:x} filesz=0x{ph['filesz']:x}")
            return


def featenabler_compare():
    """featenabler partition ELF vs modem/image/featenabler.mdt+bXX merge."""
    img = os.path.join(TEE, "featenabler.img")
    with open(img, "rb") as f:
        data = f.read()

    def phdrs64(b):
        phoff = struct.unpack_from("<Q", b, 32)[0]
        phentsize, phnum = struct.unpack_from("<HH", b, 54)
        out = []
        for i in range(phnum):
            o = phoff + i * phentsize
            _t, off, va, _pa, fsz, _msz, _fl, _al = struct.unpack_from("<IIQQQQQQ", b, o)
            out.append((off, va, fsz))
        return out

    p = phdrs64(data)
    modem_dir = "/home/aditya/.zcode/workspace/draft-6b0eaffc-c308-4302-94d4-244a23b47158/downloads/lineage-fp6/extracted/trees/modem/image"
    with open(os.path.join(modem_dir, "featenabler.mdt"), "rb") as f:
        mdt = f.read()
    m = phdrs64(mdt)
    print(f"--- featenabler.img phnum={len(p)} vs modem/image/featenabler.mdt phnum={len(m)}")
    layout_match = len(p) == len(m) and all(
        pv == mv and pf == mf for (_po, pv, pf), (_mo, mv, mf) in zip(p, m))
    print(f"    9-segment vaddr/filesz tables identical: {layout_match}")
    # byte-match spot check on plain data segments (skip header-block segs)
    checked = matched = 0
    for i, ((off, va, fsz), (mo_, mva, mfsz)) in enumerate(zip(p, m)):
        bpath = os.path.join(modem_dir, f"featenabler.b{i:02d}")
        with open(bpath, "rb") as f:
            bxx = f.read()
        bphoff = struct.unpack_from("<Q", bxx, 32)[0]
        bphentsize, bphnum = struct.unpack_from("<HH", bxx, 54)
        seg = bxx[bphoff + bphentsize * bphnum:]
        if len(seg) == fsz:  # clean 1:1 segment files only
            checked += 1
            matched += seg == data[off:off + fsz]
    print(f"    byte-identical segments: {matched}/{checked} (clean 1:1 files)")


census = json.load(open(CENSUS))

print("=" * 30, "BLUETOOTH TLV CONTAINERS")
for name in ("msbtfw11.tlv", "msbtfw12.tlv", "evrbtfw20.tlv"):
    print(json.dumps(tlv_decode(os.path.join(BT, name)), indent=1))

print("=" * 30, "BLUETOOTH NVM FILES")
for name in ("msnv11.bin", "msnv12.bin", "evrnv20.bin"):
    d = nvm_decode(os.path.join(BT, name))
    print(json.dumps({k: d[k] for k in ("file", "size", "headers", "tail_unparsed")}))
    for t in d["tags"][:4]:
        print("   ", t)
    print(f"    ({len(d['tags'])} tags total)")

print("=" * 30, "BLUETOOTH ELF .mbn SEGMENTS")
for name in ("msbtfw11.mbn", "msbtfw12.mbn"):
    print_phdrs(census, "bluetooth/image/" + name)

print("=" * 30, "TRUSTZONE PARTITION ELFS")
for name in ("trustzone/tz.img", "trustzone/hyp.img", "trustzone/keymaster.img",
             "trustzone/devcfg.img", "tee-apps/uefisecapp.img",
             "tee-apps/multiimgoem.img", "tee-apps/featenabler.img"):
    print_phdrs(census, name)

print("=" * 30, "VERSION STRINGS")
for sub, name in ((BT, "msbtfw11.mbn"), (BT, "msbtfw12.mbn"),
                  (TZ, "tz.img"), (TZ, "hyp.img"), (TZ, "keymaster.img"),
                  (TZ, "devcfg.img"), (TEE, "uefisecapp.img"),
                  (TEE, "multiimgoem.img"), (TEE, "featenabler.img")):
    print(f"--- {name}")
    for s in strings_version(os.path.join(sub, name)):
        print("   ", s)

print("=" * 30, "FEATENABLER CROSS-CHECK (partition vs modem/image merge)")
featenabler_compare()
