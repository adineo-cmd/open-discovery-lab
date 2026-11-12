#!/usr/bin/env python3
"""Psion Series 3 AIK Audio (AICASoundFile) decoder - F-44 (Track C, R-5 follow-up to F-39).

Cracks the nibble->amplitude codebook family for the AICA sound compressor body:

  container  : 15-char magic "AICASoundFile**" + NUL, u16-BE N @0x12, filesize == 32 + N*128
  body       : N frames x 128 bytes = N x 256 4-bit nibble codes
  nibble     : bit3 = sign, bits2-0 = magnitude index into a per-magnitude LEVEL table L
  sample     : unit-step closed-loop DPCM:  x[n] = clip(x[n-1] +- L[mag], -128, 127)
  silence    : codes 5 and 13 (mag 5, both signs) have L = 0  -> zero diff -> held value

Best-fit level table (TETRIS_2/3/4, empirical perm search, see docs/psion-aik-decode.md):

  L[mag 0..7] = [2, 1, 7, 4, 6, 0, 0, 3]

  i.e. diff(code) = -(L) for codes 8..15, +(L) for codes 0..7, with hold (zero-diff)
  codes 5/13 and 6/14. Residual ambiguity: +/-1 on the small-level assignment
  (mags 0,1,7 <-> levels 0..3); top candidates within 0.5 dB SFM.

Predictor scope: per-256-nibble frame reset decode is the only clip-free bounded
variant (full-file carry drifts monotonically into the -128 rail; per-frame 1-byte
predictor seed refuted). Residual frame-boundary discontinuities in the reset
decode (mean jump 26-70 vs median sample step 2) remain an open item.

Rate: not independently arbitrated; structure decodes identically at 4096/8192 Hz.
Census N-unit hypothesis (frame = 1/32 s) gives 8192 Hz.

Usage: python3 psion_aik_decode.py FILE.AIK [out.wav] [rate]
Stdlib only.
"""
import struct, sys, wave

MAGIC = b"AICASoundFile**"

# best-fit level table (see doc); L[5]=0 is the silence anchor, exact per-magnitude
# assignment of levels 0..3 between mags 0,1,7 is uncertain (+/-1)
LEVELS = [2, 1, 7, 4, 6, 0, 0, 3]

def load(path):
    data = open(path, "rb").read()
    if data[:15] != MAGIC or data[15] != 0:
        raise ValueError("not an AICASoundFile")
    n = struct.unpack(">H", data[18:20])[0]
    body = data[32:]
    if len(body) != n * 128:
        raise ValueError("size rule violated: %d != 32 + %d*128" % (len(data), n))
    return n, body

def nibbles(body, hi_first=True):
    out = []
    for b in body:
        hi, lo = b >> 4, b & 0xF
        out += [hi, lo] if hi_first else [lo, hi]
    return out

def decode(codes, levels=LEVELS, reset_frame=True):
    """Unit-step signed-magnitude DPCM, predictor reset per 256-nibble frame."""
    x = [0] * len(codes)
    prev = 0
    for i, c in enumerate(codes):
        if reset_frame and i % 256 == 0:
            prev = 0
        d = levels[c & 7]
        if c & 8:
            d = -d
        prev += d
        if prev > 127:
            prev = 127
        elif prev < -128:
            prev = -128
        x[i] = prev
    return x

def write_wav(path, x, rate):
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(1); w.setframerate(rate)
        w.writeframes(bytes(((v + 128) & 0xFF) for v in x))

def main():
    if len(sys.argv) < 2:
        print(__doc__); return 1
    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else src.rsplit(".", 1)[0] + "_decoded.wav"
    rate = int(sys.argv[3]) if len(sys.argv) > 3 else 8192
    n, body = load(src)
    codes = nibbles(body, hi_first=True)
    x = decode(codes)
    write_wav(out, x, rate)
    hist = [0] * 16
    for c in codes:
        hist[c] += 1
    print("decoded %s: N=%d frames, %d samples, rate=%d Hz, nibble hist=%s"
          % (src, n, len(x), rate, hist))
    print("wrote", out)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
