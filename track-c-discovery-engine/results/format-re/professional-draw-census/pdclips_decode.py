#!/usr/bin/env python3
"""
Professional Draw (Amiga) decoder - partial, stdlib only.
Cracked container: 'PDPF' + u32be total-file-size, then flat IFF-style chunks
(4CC + u32be size + payload) with zero-length marker chunks (COLR/CLIP/OBJ/OEND/...)
bracketing sections (CFIN/OFIN/CLFN terminators). Document files (.pdraw) use a
different header: 08 08 09 0f + NUL-terminated 'Professional Draw Vn.nn' + fields,
then P-chunks (PENV/PDOC/PPAG/PBOX/PSGR); full walk does NOT complete on .pdraw.
Output: JSON metadata per file (palette, clips, objects, validation).
"""
import sys, os, json, struct

def parse_chunks(buf, off, end):
    chunks = []; pos = off
    while pos + 8 <= end:
        ctype = buf[pos:pos+4]
        if not all(32 <= b < 127 for b in ctype):
            return chunks, pos, "non-4cc@%#x:%s" % (pos, ctype.hex())
        clen = struct.unpack(">I", buf[pos+4:pos+8])[0]
        nxt = pos + 8 + clen
        if nxt > end:
            return chunks, pos, "overrun@%#x" % pos
        chunks.append((ctype.decode(), pos, clen, buf[pos+8:nxt]))
        pos = nxt
    return chunks, pos, None if pos == end else "tail-gap:%d" % (end - pos)

def srgb8(p):  # SRGB payload: u16be r,g,b (0x0F-scale) + 2 pad -> 8-bit
    if len(p) < 6: return None
    return [round(v / 0x0F * 255) for v in struct.unpack(">HHH", p[:6])]

def decode_pdpf(path):
    data = open(path, "rb").read()
    out = {"file": os.path.basename(path), "size": len(data),
           "declared_size": struct.unpack(">I", data[4:8])[0]}
    out["size_match"] = out["declared_size"] == out["size"]
    chunks, endpos, err = parse_chunks(data, 8, len(data))
    out["chunk_count"] = len(chunks); out["parse_error"] = err
    out["bytes_accounted"] = endpos == len(data)
    palette, clips, objs, cur_clip, cur_obj = [], [], [], None, None
    for t, off, clen, p in chunks:
        if t == "CNAM": curc = {"name": p.rstrip(b"\x00").decode("latin1")}; palette.append(curc)
        elif t == "SRGB" and palette: palette[-1]["srgb8"] = srgb8(p)
        elif t == "PYMC" and palette: palette[-1]["cmyk_u16"] = list(struct.unpack(">HHHH", p[:8])) if len(p) >= 8 else None
        elif t == "CLNM": cur_clip = {"name": p.rstrip(b"\x00").decode("latin1"), "objects": []}; clips.append(cur_clip)
        elif t == "VBOX":
            v = list(struct.unpack(">IIII", p[:16])) if len(p) >= 16 else None
            if cur_obj is not None and cur_obj.get("vbox") is None: cur_obj["vbox"] = v
            elif cur_clip is not None and cur_clip.get("vbox") is None: cur_clip["vbox"] = v
        elif t == "DBOX":
            v = list(struct.unpack(">iiii", p[:16])) if len(p) >= 16 else None
            if cur_obj is not None and cur_obj.get("dbox") is None: cur_obj["dbox"] = v
        elif t == "OBJ ": cur_obj = {"type": p.decode("latin1", "replace")}; (cur_clip["objects"] if cur_clip else objs).append(cur_obj)
        elif t == "OFLG" and cur_obj is not None: cur_obj["oflg"] = struct.unpack(">I", p[:4])[0] if len(p) >= 4 else None
        elif t == "LINE" and cur_obj is not None: cur_obj["line_w"] = struct.unpack(">H", p[:2])[0] if len(p) >= 2 else None
        elif t == "FILL" and cur_obj is not None: cur_obj["fill"] = struct.unpack(">H", p[:2])[0] if len(p) >= 2 else None
        elif t == "STXT": (cur_clip["objects"] if cur_clip else objs).append({"type": "STXT", "raw16": list(struct.unpack(">9h", p[:18])) if len(p) >= 18 else None})
        elif t == "DATA" and cur_obj is not None: cur_obj["data_len"] = clen
        elif t == "OEND": cur_obj = None
    out["palette"] = palette; out["clips"] = clips; out["loose_objects"] = objs
    return out

def decode_pdraw_doc(path):
    data = open(path, "rb").read()
    out = {"file": os.path.basename(path), "size": len(data), "kind": "pdraw-document"}
    out["magic4"] = data[:4].hex()
    nul = data.find(b"\x00", 4)
    out["version_string"] = data[4:nul].decode("latin1", "replace")
    out["header_u32be@0x66_6a_6e_72"] = [struct.unpack(">I", data[o:o+4])[0] for o in (0x66, 0x6a, 0x6e, 0x72)]
    i = data.find(b"PENV")
    chunks, endpos, err = parse_chunks(data, i, len(data))
    out["top_chunks"] = [t for t, _, _, _ in chunks]; out["top_chunk_count"] = len(chunks)
    out["walk_stops_at"] = hex(endpos); out["walk_error"] = err
    return out

def main():
    res = [decode_pdpf(p) if open(p, "rb").read(4) == b"PDPF" else decode_pdraw_doc(p) for p in sys.argv[1:]]
    print(json.dumps(res, indent=1))

main()
