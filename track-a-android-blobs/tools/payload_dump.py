#!/usr/bin/env python3
"""Dump one partition from an Android OTA payload.bin without protobuf.

Companion to payload_manifest.py (same empirical field numbering, payload
version 2 / minor_version 4096):
  PartitionUpdate: name=1, PartitionInfo=7 {size=1}, InstallOperation=8
  InstallOperation: type=1, data_offset=2, data_length=3, dst_extent=6
  Extent: start_block=1, num_blocks=2
Ops supported: REPLACE (raw), REPLACE_XZ (lzma/xz), REPLACE_BZ (bzip2).
Usage: payload_dump.py payload.bin partition_name out.img
"""
import struct
import sys
import lzma
import bz2

# NOTE: in the update_engine payload enum, REPLACE_BZ (type 1) is *bzip2*
# (verified empirically: op payloads carry the "BZh9" magic), not brotli.

OP_REPLACE = 0
OP_REPLACE_XZ = 8
OP_REPLACE_BZ = 1


def read_varint(buf, i):
    shift = val = 0
    while True:
        b = buf[i]
        i += 1
        val |= (b & 0x7F) << shift
        if not b & 0x80:
            return val, i
        shift += 7


def fields(buf):
    i = 0
    while i < len(buf):
        tag, i = read_varint(buf, i)
        fnum, wt = tag >> 3, tag & 7
        if wt == 0:
            v, i = read_varint(buf, i)
            yield fnum, wt, v
        elif wt == 2:
            ln, i = read_varint(buf, i)
            yield fnum, wt, buf[i:i + ln]
            i += ln
        elif wt == 5:
            yield fnum, wt, buf[i:i + 4]
            i += 4
        elif wt == 1:
            yield fnum, wt, buf[i:i + 8]
            i += 8
        else:
            raise ValueError(f"wire type {wt}")


def parse(msg):
    return list(fields(msg))


def main(payload_path, target, out_path):
    with open(payload_path, "rb") as f:
        hdr = f.read(24)
        magic, ver, man_len, sig_len = struct.unpack(">4sQQI", hdr[:24])
        assert magic == b"CrAU"
        blob_base = 24 + man_len + sig_len
        manifest = f.read(man_len)

    part = None
    for fnum, wt, v in parse(manifest):
        if fnum == 13 and wt == 2:
            name = size = None
            for f2, w2, v2 in parse(v):
                if f2 == 1 and w2 == 2:
                    name = v2.decode()
            if name == target:
                part = v
                break
    if part is None:
        sys.exit(f"partition {target!r} not in manifest")

    info = dict(name=name, size=None, ops=[])
    for f2, w2, v2 in parse(part):
        if f2 == 7 and w2 == 2:
            for f3, w3, v3 in parse(v2):
                if f3 == 1 and w3 == 0:
                    info["size"] = v3
        elif f2 == 8 and w2 == 2:
            op = {"type": None, "off": None, "len": None, "start": None, "blocks": None}
            for f3, w3, v3 in parse(v2):
                if f3 == 1 and w3 == 0:
                    op["type"] = v3
                elif f3 == 2 and w3 == 0:
                    op["off"] = v3
                elif f3 == 3 and w3 == 0:
                    op["len"] = v3
                elif f3 == 6 and w3 == 2:
                    for f4, w4, v4 in parse(v3):
                        if f4 == 1 and w4 == 0:
                            op["start"] = v4
                        elif f4 == 2 and w4 == 0:
                            op["blocks"] = v4
            info["ops"].append(op)

    n_ops = len(info["ops"])
    print(f"{target}: size {info['size']}, {n_ops} ops")
    out = bytearray(info["size"])
    with open(payload_path, "rb") as f:
        for n, op in enumerate(info["ops"], 1):
            f.seek(blob_base + op["off"])
            data = f.read(op["len"])
            if op["type"] == OP_REPLACE:
                dec = data
            elif op["type"] == OP_REPLACE_XZ:
                dec = lzma.decompress(data)
            elif op["type"] == OP_REPLACE_BZ:
                dec = bz2.decompress(data)
            else:
                raise RuntimeError(f"unsupported op type {op['type']}")
            dst = op["start"] * 4096
            if len(dec) != op["blocks"] * 4096:
                raise RuntimeError(
                    f"op {n}: decoded {len(dec)} != {op['blocks'] * 4096}")
            out[dst:dst + len(dec)] = dec
            print(f"  op {n}/{n_ops}: type {op['type']}, {op['len']} -> "
                  f"{len(dec)} bytes @ block {op['start']}")
    with open(out_path, "wb") as g:
        g.write(out)
    print(f"wrote {out_path} ({len(out)} bytes)")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
