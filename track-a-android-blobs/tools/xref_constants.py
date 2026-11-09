#!/usr/bin/env python3
"""xref_constants.py — scan wpss firmware segments for ath11k protocol constants.

First-pass firmware↔driver cross-reference: search raw segment bytes for
little-endian 16/32-bit encodings of ath11k's HTC service/message IDs.
NOTE: superseded by xref_immediates.py — raw byte scans are too noisy for
small constants (documented in docs/wpss-qurt-rtos.md).

Usage: python3 xref_constants.py <segment> [<segment>...]
"""
import struct
import sys

HTC_MSGS = {
    "HTC_MSG_READY": 1,
    "HTC_MSG_CONNECT_SERVICE": 2,
    "HTC_MSG_CONNECT_SERVICE_RESP": 3,
    "HTC_MSG_SETUP_COMPLETE": 4,
    "HTC_MSG_SEND_SUSPEND_COMPLETE": 6,
}

SVC_GRPS = {
    "GRP_WMI": 1,
    "GRP_NMI": 2,
    "GRP_HTT": 3,
    "GRP_CFG": 4,
    "GRP_IPA": 5,
    "GRP_PKTLOG": 6,
    "GRP_TEST": 254,
}

CONSTS = {}
for name, v in HTC_MSGS.items():
    CONSTS[f"msg:{name}"] = v
for gname, g in SVC_GRPS.items():
    for idx in range(0, 7):
        sid = (g << 8) | idx
        CONSTS[f"svc:{gname}.{idx}"] = sid


def scan(path, consts):
    data = open(path, "rb").read()
    hits = {}
    for name, v in consts.items():
        if v < 0x100:
            continue  # 1-byte values too noisy
        p16 = struct.pack("<H", v)
        n16 = data.count(p16)
        p32 = struct.pack("<I", v)
        n32 = data.count(p32)
        if n16 or n32:
            hits[name] = (v, n16, n32)
    return hits


def main():
    for path in sys.argv[1:]:
        hits = scan(path, CONSTS)
        print(f"== {path.split('/')[-1]} ==")
        if not hits:
            print("  no constant hits")
        for name in sorted(hits, key=lambda k: -(hits[k][1] + hits[k][2])):
            v, n16, n32 = hits[name]
            print(f"  {name:<38} val=0x{v:04x}  LE16×{n16}  LE32×{n32}")


if __name__ == "__main__":
    main()
