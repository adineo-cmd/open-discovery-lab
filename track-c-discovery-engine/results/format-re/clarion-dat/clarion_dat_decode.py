#!/usr/bin/env python3
"""clarion_dat_decode.py — decoder/schema-parser for legacy Clarion (2.x/Professional Developer era) .DAT database files.

Pure stdlib. Validated against 43 plain + 2 header-cracked encrypted samples
(sembiance.com/fileFormatSamples/document/clarionDatabase, 2026-11-12).

Structure summary (validated, see clarion-dat-format.md):
  85-byte header (LE), field descriptors 27 B each, key descriptors (19 + 6*numcomps),
  picture descriptors (2 + piclen), array descriptors (6 + 4*ndim),
  then numrecs fixed-length record slots of reclen bytes, each slot = 5-byte record
  header (rhd u8, rptr u32) + data.  filesize == offset + numrecs * reclen (43/43).
  Whole file (past sig+sfatr) may be 2-byte XOR encrypted (per-file key, phase reset
  at section boundaries: header@0x04, descriptors@0x55, each 27-byte field descriptor).

Usage: python3 clarion_dat_decode.py FILE
"""
import sys, json, struct

FLDTYPE = {1: "LONG", 2: "REAL", 3: "STRING", 4: "STRING+PICTURE", 5: "BYTE", 6: "SHORT", 7: "GROUP", 8: "DECIMAL"}
SFATR_BITS = ["locked", "owned", "encrypted", "memo-exists", "compressed", "reclaim-deleted", "read-only", "may-create"]

def u16(b, o): return b[o] | (b[o+1] << 8)
def u32(b, o): return b[o] | (b[o+1] << 8) | (b[o+2] << 16) | (b[o+3] << 24)

def dec_time(v):
    if not (1 <= v <= 8640000): return None
    v -= 1
    return "%02d:%02d:%02d.%02d" % (v // 360000, (v % 360000) // 6000, (v % 6000) // 100, v % 100)

def dec_date(v):
    if not (4 <= v <= 109211): return None
    d = v - 3 if v > 36527 else v - 4
    year = 1801 + 4 * (d // 1461)
    r = d % 1461
    if r != 0:
        year += r // 365; day = r % 365
    else:
        year += 3; day = 365
    if year < 100: year += 1900
    ml = [31, 29 if (year % 4 == 0 and year != 1900) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    m = 1
    for L in ml:
        if day < L: break
        day -= L; m += 1
    return "%04d-%02d-%02d" % (year, m, day + 1)

def find_header_key(raw):
    """Brute-force 2-byte XOR key for the encrypted header (anchored at 0x04)."""
    for k in range(65536):
        kb = bytes([k & 0xFF, k >> 8])
        d = bytearray(raw[:0x55])
        for i in range(4, 0x55):
            d[i] = raw[i] ^ kb[(i - 4) % 2]
        numflds = u16(d, 0xD); reclen = u16(d, 0x13); offset = u32(d, 0x15)
        if not (1 <= numflds <= 60 and 10 <= reclen <= 60000): continue
        if not (0x55 <= offset <= len(raw)): continue
        if numflds * 27 + 0x55 > offset: continue
        if d[4] > 10: continue
        if offset != 0x55 + numflds * 27 + d[4] * 19: continue
        return bytes(d), kb
    return None, None

def parse(raw, key_hex=None):
    b = raw
    key = bytes.fromhex(key_hex) if key_hex else None
    encrypted = bool(u16(b, 2) & 0x04) or key is not None
    off_data = None
    if encrypted:
        if key is None:
            h55, key = find_header_key(raw)
            if h55 is None:
                return {"error": "encrypted header; 2-byte key brute force failed"}
        b = bytearray(raw)
        for i in range(4, min(0x55, len(raw))):
            b[i] = raw[i] ^ key[(i - 4) % 2]
        off_data = (b[0x15] | (b[0x16] << 8) | (b[0x17] << 16) | (b[0x18] << 24)) if len(b) >= 0x19 else len(raw)
        for i in range(0x55, min(off_data if 0x55 <= off_data <= len(raw) else len(raw), len(raw))):
            b[i] = raw[i] ^ key[(i - 0x55) % 2]
        b = bytes(b)
    h = {
        "sig": b[0:2].decode("latin1"), "sig_le": u16(b, 0),
        "sfatr": u16(b, 2), "sfatr_bits": [n for i, n in enumerate(SFATR_BITS) if u16(b, 2) & (1 << i)],
        "numbkeys": b[4], "numrecs": u32(b, 5), "numdels": u32(b, 9),
        "numflds": u16(b, 0xD), "numpics": u16(b, 0xF), "numarrs": u16(b, 0x11),
        "reclen": u16(b, 0x13), "offset": u32(b, 0x15),
        "logeof": u32(b, 0x19), "logbof": u32(b, 0x1D), "freerec": u32(b, 0x21),
        "recnam": b[0x25:0x31].decode("latin1").rstrip(chr(0) + " "),
        "memnam": b[0x31:0x3D].decode("latin1").rstrip(chr(0) + " "),
        "filpre": b[0x3D:0x40].decode("latin1").rstrip(chr(0) + " "),
        "recpre": b[0x40:0x43].decode("latin1").rstrip(chr(0) + " "),
        "memolen": u16(b, 0x43), "memowid": u16(b, 0x45),
        "chgtime": dec_time(u32(b, 0x4B)), "chgdate": dec_date(u32(b, 0x4F)),
    }
    ko = 0x55 + h["numflds"] * 27
    keys = []
    for _ in range(h["numbkeys"]):
        nc = b[ko]
        parts = []
        po = ko + 19
        for _ in range(nc):
            parts.append({"fldtype": FLDTYPE.get(b[po]), "fldnum": u16(b, po+1), "elmoff": u16(b, po+3), "elmlen": b[po+5]})
            po += 6
        keys.append({"keyname": b[ko+1:ko+17].decode("latin1").rstrip(chr(0) + " "), "comptype": b[ko+17], "complen": b[ko+18], "parts": parts})
        ko = po
    pics = []
    for _ in range(h["numpics"]):
        pl = u16(b, ko)
        pics.append(b[ko+2:ko+2+pl].decode("latin1"))
        ko += 2 + pl
    arrs = []
    for _ in range(h["numarrs"]):
        nd = u16(b, ko); td = u16(b, ko+2); es = u16(b, ko+4); ko += 6
        dims = []
        for _ in range(min(nd or td, 8)):
            dims.append([u16(b, ko), u16(b, ko+2)]); ko += 4
        arrs.append({"numdim": nd, "totdim": td, "elmsiz": es, "dims": dims})
    fields = []
    for i in range(h["numflds"]):
        o = 0x55 + i * 27
        if encrypted:
            # keystream phase resets at each 27-byte field descriptor (validated on GENESOFT/GEORGEA)
            seg = bytes(raw[o+t] ^ key[t % 2] for t in range(min(27, len(raw) - o)))
            fd = seg
        else:
            fd = b
        fields.append({"fldnum": i + 1, "type": FLDTYPE.get(fd[0], "?%d" % fd[0]),
                       "name": fd[1:17].decode("latin1").rstrip(chr(0) + " "),
                       "foffset": u16(fd, 17), "length": u16(fd, 19),
                       "decsig": fd[21], "decdec": fd[22], "arrnum": u16(fd, 23), "picnum": u16(fd, 25)})
    h["keys"], h["pictures"], h["arrays"], h["fields"] = keys, pics, arrs, fields
    h["desc_end"] = ko
    h["checks"] = {
        "desc_end_eq_offset": ko == h["offset"],
        "size_eq": len(raw) == h["offset"] + h["numrecs"] * h["reclen"],
    }
    h["encrypted"] = encrypted
    if encrypted: h["header_key"] = key.hex()
    return h

def field_value(f, buf):
    v = buf[f["foffset"]:f["foffset"] + f["length"]]
    t = f["type"]
    if t in ("STRING", "STRING+PICTURE"):
        return v.decode("latin1").rstrip(chr(0) + " ")
    if t == "LONG": return struct.unpack("<i", v[:4])[0]
    if t == "SHORT": return struct.unpack("<h", v[:2])[0]
    if t == "REAL": return struct.unpack("<d", v[:8])[0]
    if t == "BYTE": return v[0]
    if t == "DECIMAL":
        digs = "".join("%x" % (c >> 4) + "%x" % (c & 15) for c in v)
        return {"digits": digs, "decsig": f["decsig"], "decdec": f["decdec"]}
    if t == "GROUP": return None  # container only
    return v.hex()

def records(h, raw, key_hex=None, max_records=None):
    key = bytes.fromhex(key_hex) if key_hex else None
    out = []
    for i in range(h["numrecs"]):
        o = h["offset"] + i * h["reclen"]
        rec = bytearray(raw[o:o + h["reclen"]])
        if h["encrypted"]:
            if key is None and h.get("header_key"): key = bytes.fromhex(h["header_key"])
            for j in range(len(rec)):
                rec[j] = raw[o + j] ^ key[j % 2]
        if len(rec) < 5: break
        row = {"recnum": i + 1, "rhd": rec[0], "rhd_bits": [n for k, n in enumerate(["new", "old", "revised", "r3", "deleted", "r5", "held", "r7"]) if rec[0] & (1 << k)], "rptr": u32(rec, 1)}
        for f in h["fields"]:
            if f["type"] == "GROUP": continue
            val = field_value(f, rec[5:])
            row[f["name"] or "field%d" % f["fldnum"]] = val
        out.append(row)
        if max_records and len(out) >= max_records: break
    return out

def main():
    if len(sys.argv) < 2:
        print(__doc__); return 1
    fn = sys.argv[1]
    raw = open(fn, "rb").read()
    h = parse(raw)
    print(json.dumps(h, indent=1))
    if not h.get("encrypted") or h.get("header_key"):
        recs = records(h, raw, h.get("header_key"), max_records=10)
        for r in recs:
            print(json.dumps(r))
    return 0

if __name__ == "__main__":
    sys.exit(main())
