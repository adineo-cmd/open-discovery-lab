#!/usr/bin/env python3
"""Minimal read-only OTA payload.bin manifest parser (no protobuf dep).

Parses the ChromeOS update_engine payload header + DeltaArchiveManifest
wire format just deep enough to list partitions, sizes and operation types.
Field numbers per AOSP system/update_engine/update_metadata.proto:
  DeltaArchiveManifest: partitions=2 (repeated PartitionUpdate)
  PartitionUpdate: partition_name=1, new_partition_size=4, operations=5
  InstallOperation: type=1, data_offset=2, data_length=3, dst_extent=4, src_extent=5
  Extent: start_block=1, num_blocks=2
  InstallOperation.Type: REPLACE=0 REPLACE_BZ=1 MOVE=2 BSDIFF=3 SOURCE_COPY=4
                         SOURCE_BSDIFF=5 ZERO=6 DISCARD=7 REPLACE_XZ=8
                         PUFFDIFF=9 SOURCE_BROTLI=10

NOTE (empirical, FP6 lineage-23.2 payload): payload v2 (minor_version 4096)
uses a renumbered manifest — partitions live at field 13, PartitionInfo at
field 7 ({size=1}), InstallOperation at field 8 with dst_extent=6. Both
numberings are accepted below.
"""
import struct
import sys
import collections

OP_NAMES = {0: "REPLACE", 1: "REPLACE_BZ (= bzip2)", 2: "MOVE", 3: "BSDIFF",
            4: "SOURCE_COPY", 5: "SOURCE_BSDIFF", 6: "ZERO", 7: "DISCARD",
            8: "REPLACE_XZ", 9: "PUFFDIFF", 10: "SOURCE_BROTLI"}


def read_varint(buf, i):
    shift = 0
    val = 0
    while True:
        b = buf[i]
        i += 1
        val |= (b & 0x7F) << shift
        if not b & 0x80:
            return val, i
        shift += 7


def fields(buf):
    """Yield (field_number, wire_type, value_bytes_or_int)."""
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


def op_type(opbuf):
    t = None
    for fnum, wt, v in fields(opbuf):
        if fnum == 1 and wt == 0:
            t = v
    return t


def main(path):
    with open(path, "rb") as f:
        hdr = f.read(24)
        magic, ver, man_len, sig_len = struct.unpack(">4sQQI", hdr[:24])
        assert magic == b"CrAU", magic
        manifest = f.read(man_len)  # manifest follows header directly; signatures after

    partitions = []
    parts = []
    for fnum, wt, val in fields(manifest):
        # empirical: payload v2 (minor_version 4096) puts partitions at field 13
        if fnum == 2 and wt == 2:  # legacy numbering
            parts.append(val)
        if fnum == 13 and wt == 2:
            parts.append(val)

    for val in parts:
        name = None
        size = None
        ops = []
        for f2, w2, v2 in fields(val):
            if f2 == 1 and w2 == 2:
                name = v2.decode()
            elif f2 == 7 and w2 == 2:  # PartitionInfo: f1=size, f2=hash
                for f3, w3, v3 in fields(v2):
                    if f3 == 1 and w3 == 0:
                        size = v3
            elif f2 == 5 and w2 == 2:  # legacy InstallOperation
                ops.append(op_type(v2))
            elif f2 == 8 and w2 == 2:  # payload-v2 InstallOperation
                ops.append(op_type(v2))
        partitions.append((name, size, ops))

    print(f"{len(partitions)} partitions in manifest\n")
    print(f"{'name':<22}{'size':>12}  ops")
    for name, size, ops in partitions:
        hist = dict(collections.Counter(OP_NAMES.get(o, o) for o in ops))
        print(f"{name:<22}{size or '?':>12}  {hist}")


if __name__ == "__main__":
    main(sys.argv[1])
