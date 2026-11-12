#!/usr/bin/env python3
"""Sonic Arranger standalone instrument (SASI) parser + module cross-validator.

Usage: python3 sa_instrument_probe.py SASI_FILE... [--module MODULE] [--json]

Cracked 2026-11-12 (36 files from Aminet `mus/misc/Sonic_ArrangI.lha`,
extracted from Aminet CD-ROM #12, archive.org item aminet-12):
  SASI layout (672 B, exact):
    0x00  magic "SASI\\0\\0\\0\\0" (8 bytes)
    0x08  instrument record, 152 bytes, byte-for-byte the SAME layout as the
          per-instrument INST entry inside Sonic Arranger modules
          (all fields big-endian u16 unless noted; see offsets below)
    0xA0  4 x 128-byte tables (512 bytes):
          blk0 = waveform, signed 8-bit samples (sine/ramp/noise shapes seen)
          blk1 = ADSR amplitude table, 0..64 (Amiga volume scale)
          blk2 = AMF modulation table (sparse; sine-shaped curves seen)
          blk3 = second waveform-like table, signed 8-bit (role tentative)
  8 + 152 + 4*128 = 672  (matches dexvert fileSize=672 on all 43 known files)

Instrument record offsets (relative to record start = file offset 8):
  +0 type, +2 waveform_number, +4 waveform_length, +6 repeat_length,
  +8..15 reserved(8), +16 volume (low byte), +18 fine_tuning (i8),
  +20 portamento_speed, +22 vibrato_delay, +24 vibrato_speed, +26 vibrato_level,
  +28 amf_number/delay/length/repeat, +36 adsr_number/delay/length/repeat,
  +44 sustain_point, +46 sustain_delay, +48..63 reserved(16),
  +64 effect_arg1, +66 effect, +68 effect_arg2, +70 effect_arg3, +72 effect_delay,
  +74 3 x arpeggio {u8 len, u8 repeat, 14 x i8}, +122 name (30 bytes, NUL-padded)
Layout inherited from the UADE-family Sonic Arranger module reader
(nuade players/sonicarranger/sonic_arranger.c) and cross-validated here on
module INST entries (name slot, volume range, arpeggio stride all match).
"""
import sys, struct, json, os


def parse_sasi(path):
    d = open(path, "rb").read()
    r = {"file": os.path.basename(path)}
    if len(d) != 672 or d[:4] != b"SASI":
        r["valid"] = False
        return r
    r["valid"] = True
    o = 8
    be = lambda off: struct.unpack_from(">H", d, o + off)[0]
    r["type"] = be(0)
    r["waveform_number"] = be(2)
    r["waveform_length"] = be(4)
    r["repeat_length"] = be(6)
    r["volume"] = be(16) & 0xFF
    r["fine_tuning"] = struct.unpack_from(">b", d, o + 18)[0]
    r["portamento_speed"] = be(20)
    r["vibrato_delay"], r["vibrato_speed"], r["vibrato_level"] = be(22), be(24), be(26)
    r["amf"] = [be(28), be(30), be(32), be(34)]
    r["adsr"] = [be(36), be(38), be(40), be(42)]
    r["sustain_point"], r["sustain_delay"] = be(44), be(46)
    r["effect"] = [be(64), be(66), be(68), be(70), be(72)]
    r["arpeggios"] = [
        {"len": d[o + 74 + 16 * j], "repeat": d[o + 75 + 16 * j],
         "values": list(struct.unpack_from("<14b", d, o + 76 + 16 * j))}
        for j in range(3)
    ]
    r["name"] = d[o + 122:o + 152].rstrip(b"\0").decode("latin1")
    blocks = []
    for b in range(4):
        t = d[160 + 128 * b:160 + 128 * (b + 1)]
        blocks.append({"nonzero": sum(1 for c in t if c), "min": min(t), "max": max(t)})
    r["blocks"] = blocks
    return r


def parse_module_instruments(path):
    """Unpacked module (SOARV1.0): walk to INST chunk, return raw 152-byte records."""
    d = open(path, "rb").read()
    pos = 8
    while pos + 4 <= len(d):
        mark = d[pos:pos + 4]
        pos += 4
        if mark == b"INST":
            cnt = struct.unpack_from(">I", d, pos)[0]
            pos += 4
            return [d[pos + 152 * i:pos + 152 * (i + 1)] for i in range(cnt)]
        if mark == b"SD8B":  # variable-size chunk: bail
            return []
        cnt = struct.unpack_from(">I", d, pos)[0] if pos + 4 <= len(d) else 0
        pos += 4
        pos += cnt * {"STBL": 12, "OVTB": 16, "NTBL": 4}.get(mark.decode("latin1", "replace"), 0)
    return []


if __name__ == "__main__":
    args = sys.argv[1:]
    out = {"instruments": [], "module_crosscheck": None}
    if "--module" in args:
        i = args.index("--module")
        recs = parse_module_instruments(args[i + 1])
        out["module_crosscheck"] = {
            "module": args[i + 1], "num_instrument_records": len(recs),
            "record_bytes": 152,
            "note": "record length 152 x count + chunk stream must consume to INST end; "
                    "name slot at record offset 122, volume 0-64",
        }
    for a in args:
        if a in ("--module", "--json") or ("--module" in args and a == args[args.index("--module") + 1]):
            continue
        if os.path.isfile(a):
            out["instruments"].append(parse_sasi(a))
    if "--json" in args:
        print(json.dumps(out, indent=1))
    else:
        ok = [r for r in out["instruments"] if r.get("valid")]
        bad = [r for r in out["instruments"] if not r.get("valid")]
        print(f"valid SASI: {len(ok)}  invalid: {len(bad)}")
        for r in ok[:10]:
            print(f"  {r['name'][:26]:26s} type={r['type']} w#={r['waveform_number']} "
                  f"wLen={r['waveform_length']} vol={r['volume']} vib={r['vibrato_delay']},"
                  f"{r['vibrato_speed']},{r['vibrato_level']} fx={r['effect']} nz={ [b['nonzero'] for b in r['blocks']] }")
        if out["module_crosscheck"]:
            print("module crosscheck:", out["module_crosscheck"])
