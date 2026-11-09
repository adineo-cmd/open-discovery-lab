#!/usr/bin/env python3
"""xref_wmi.py — find ath11k WMI command/event IDs inside the wpss firmware.

Evaluates ath11k's wmi.h enums (implicit increments + WMI_TLV_CMD(group)
macros) the way the C compiler would, then scans firmware segments at 4-byte
alignment for the resulting LE32 values.

Usage: python3 xref_wmi.py <ath11k-wmi.h> <segment> [<segment>...]
"""
import re
import struct
import sys


def eval_wmi_h(text):
    def parse_enum_block(body, defined):
        """Evaluate one enum body, returning {name: value} (chained refs ok)."""
        body = re.sub(r"/\*.*?\*/", "", body, flags=re.S)  # strip block comments first
        out = {}
        nxt = 0
        for entry in body.split(","):
            entry = entry.strip()
            if not entry:
                continue
            m = re.match(r"([A-Za-z_][A-Za-z0-9_]*)(?:\s*=\s*(.+))?$", entry, re.S)
            if not m:
                continue
            name, expr = m.group(1), m.group(2)
            if expr is None:
                v = nxt
            else:
                try:
                    v = int(expr, 0)
                except ValueError:
                    sym = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_]*)", expr.strip())
                    if sym and sym.group(1) in out:
                        v = out[sym.group(1)]
                    elif sym and sym.group(1) in defined:
                        v = defined[sym.group(1)]
                    else:
                        m2 = re.fullmatch(
                            r"(?:WMI_TLV_CMD|WMI_CMD_GRP|WMI_EVT_GRP_START_ID)\(([A-Za-z_][A-Za-z0-9_]*)\)",
                            expr.strip())
                        if m2:
                            g = out.get(m2.group(1))
                            if g is None:
                                g = defined.get(m2.group(1))
                            v = None if g is None else ((g << 12) | 0x1)
                        else:
                            v = None
                if v is None:
                    v = nxt  # best effort
            out[name] = v
            nxt = v + 1
        return out

    # 1. group enums first (values may reference each other)
    defined = {}
    for en in re.finditer(r"enum\s+\w+\s*\{(.*?)\}", text, re.S):
        body = en.group(1)
        if "WMI_GRP_" in body:
            defined.update(parse_enum_block(body, defined))
    # 2. all enums (cmd/event IDs; may reference groups)
    results = {}
    for en in re.finditer(r"enum\s+\w+\s*\{(.*?)\}", text, re.S):
        vals = parse_enum_block(en.group(1), defined)
        defined.update(vals)
        for k, v in vals.items():
            if k.endswith("CMDID") or k.endswith("EVENTID"):
                results[k] = v
    return results


def scan(path, ids):
    data = open(path, "rb").read()
    hits = {}
    for name, v in ids.items():
        if v < 0x100:
            continue
        packed = struct.pack("<I", v)
        offs = [m.start() for m in re.finditer(re.escape(packed), data) if m.start() % 4 == 0]
        if offs:
            hits[name] = (v, len(offs), offs[0])
    return hits


def ctx(data, off, span=24):
    lo = max(0, off - span)
    words = [struct.unpack_from("<I", data, o)[0] for o in range(lo, min(len(data), off + span), 4)]
    return " ".join(f"{w:08x}" for w in words)


def main():
    wmi_h = sys.argv[1]
    ids = eval_wmi_h(open(wmi_h).read())
    print(f"evaluated {len(ids)} WMI CMDID/EVENTID values from {wmi_h}")
    for path in sys.argv[2:]:
        data = open(path, "rb").read()
        hits = scan(path, ids)
        print(f"\n== {path.split('/')[-1]} — {len(hits)} matching WMI IDs (aligned LE32) ==")
        for name in sorted(hits, key=lambda k: -hits[k][1])[:40]:
            v, n, off = hits[name]
            print(f"  {name:<46} 0x{v:04x} ×{n:<3} first@0x{off:x}")
            if n <= 3:
                print(f"      ctx: {ctx(data, off)}")


if __name__ == "__main__":
    main()
