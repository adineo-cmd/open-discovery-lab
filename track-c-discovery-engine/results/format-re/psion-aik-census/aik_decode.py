#!/usr/bin/env python3
"""Psion Series 3 AIK audio (AICASoundFile) header validator / raw-stream prober.

Usage: python3 aik_decode.py FILE.aik [--wav OUT.wav RATE]

Validated (census 2026-11-12, 3/3 samples):
  - 0x00: 15-char Pascal-prefixed magic "AICASoundFile**" + NUL (16-byte block)
  - 0x10..0x1F: info block; u16 BE at 0x12 = N, duration/blocks
  - filesize == 32 + N*128 in all samples (N = 120, 120, 60)
  - body (0x20..) = N fixed 128-byte frames of 4-bit nibble codes, 2 samples/byte
    -> N*256 samples; N*256/(N/16 s) = 4096 Hz or N*256/(N/32 s) = 8192 Hz
    (unit of N unconfirmed: 1/16 s vs 1/32 s tick; EPOC16 tick = 1/32 s)
NOT yet solved (honest negative): the nibble->amplitude code mapping.
Nibble 5 = silence (0x55 padding tails in all samples); code 2 never occurs.
The default --wav output emits both candidate mappings for listening tests.
"""
import sys, struct, wave, collections


def parse(path):
    d = open(path, "rb").read()
    if d[0:15] != b"AICASoundFile**" or d[15] != 0:
        raise ValueError("bad magic")
    n = struct.unpack_from(">H", d, 0x12)[0]
    info = {
        "file": path,
        "size": len(d),
        "duration_blocks": n,
        "size_ok": len(d) == 32 + n * 128,
        "info_block_hex": d[16:32].hex(),
        "body_bytes": len(d) - 32,
        "samples_2nib_per_byte": n * 256,
    }
    body = d[32:]
    ns = []
    for b in body:
        ns.append(b >> 4)
        ns.append(b & 15)
    info["nibble_hist"] = {k: v for k, v in sorted(collections.Counter(ns).items())}
    info["nibble2_missing"] = 2 not in info["nibble_hist"]
    info["tail_silence_55"] = body.endswith(b"\x55" * 64)
    return info, body


def emit_wav(path, body, rate):
    """Emit both candidate mappings interleaved as a stereo WAV for A/B listening:
    L = signed 4-bit two's complement, R = offset-binary (v-8). NOT a verified codec."""
    sgn, off = [], []
    for b in body:
        for v in (b >> 4, b & 15):
            sgn.append((v ^ 8) - 8 if v >= 8 else v)  # two's complement nibble
            off.append((v - 8) * 8)
    w = wave.open(path, "wb")
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(rate)
    frames = bytearray()
    for a, b in zip(sgn, off):
        frames += struct.pack("<hh", a * 256, b * 256)
    w.writeframes(bytes(frames))
    w.close()


if __name__ == "__main__":
    info, body = parse(sys.argv[1])
    for k, v in info.items():
        print(f"{k}: {v}")
    if "--wav" in sys.argv:
        i = sys.argv.index("--wav")
        emit_wav(sys.argv[i + 1], body, int(sys.argv[i + 2]))
        print("wav written (candidate mappings, unverified codec)")
