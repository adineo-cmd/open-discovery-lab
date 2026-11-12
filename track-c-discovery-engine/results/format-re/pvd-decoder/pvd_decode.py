#!/usr/bin/env python3
"""
pvd_decode.py -- standalone decoder for ProLine Voice Data (.pvd)

ProLine is Amiga BBS software with a voice-mail feature; .pvd files are its
voice/event clips.  To our knowledge (checked 2026-11-12: GitHub code search,
web search) this is the first public STANDALONE decoder for the format:
dexvert (Sembiance) detects .pvd but marks it `unsupported = true` and does
no conversion; TrID and file-signature lists only identify the magic.

Format layout (empirical, 5/5 samples consistent -- see the companion spec
docs/proline-pvd-format.md):

    0x00      u8    string length, constant 0x12 = 18
    0x01-0x12 18B   ASCII magic "Proline Voice File"
    0x13      u8    version, constant 0x01
    0x14-0x16 u24LE payload length; equals filesize - 24 in every sample
    0x17      u8    constant 0xAD = 173: candidate Amiga Paula audio period
                    (PAL clock 3546895/173 = 20501.7 Hz; NTSC 3579545/173 =
                    20685.0 Hz).  UNCONFIRMED by listening test.
    0x18..    payload (filesize-24 bytes): first and last byte are 0x00 in
                    every sample (structural delimiters; audio = payload
                    minus those two bytes).  Interior = unsigned 8-bit PCM,
                    silence floor 0x7F, one sample per byte, mono.

Sample rate: the decoder defaults to 20502 Hz (PAL Paula period from byte
0x17) and accepts --rate to test alternatives (8000, 11025, 20685 NTSC).
The rate question is documented honestly in the spec; 20502 is the best
evidenced hypothesis, not a proven fact.

Special case: some files (BOMB.PVD, and DIA.PVD partly) carry stereo
WAV-imported PCM instead of native mono recordings; BOMB.PVD additionally
embeds a mostly-intact WAVE header (11025 Hz, 2ch, 8-bit) at the start of
its audio, with the PCM truncated versus the sizes the header declares.
The decoder detects and reports this; --mode embedded honours the embedded
header (stereo WAV at the declared rate), the default --mode raw decodes
the audio bytes as mono PCM at --rate.

Usage:
    python3 pvd_decode.py INPUT.pvd [-o OUTPUT.wav] [--rate HZ]
                          [--mode raw|embedded] [--zero-floor]
                          [--keep-delimiters] [--no-wav] [--json]

Exit status 0 = decoded and (unless --no-wav) WAV written.
Requires only the Python standard library.
"""

import argparse
import json
import struct
import sys
import wave
from pathlib import Path

HEADER_SIZE = 24
MAGIC = b"Proline Voice File"
MAGIC_LEN = 0x12
VERSION = 0x01
SILENCE_BYTE = 0x7F
DEFAULT_PERIOD = 0xAD  # 173
PAULA_CLOCK_PAL = 3546895
PAULA_CLOCK_NTSC = 3579545
DEFAULT_RATE = PAULA_CLOCK_PAL // DEFAULT_PERIOD  # 20501 -> 20502


class PvdError(ValueError):
    """Raised when a file violates the structural rules of the format."""


def paula_rate(period, ntsc=False):
    """Amiga Paula output frequency for an audio period register value."""
    clock = PAULA_CLOCK_NTSC if ntsc else PAULA_CLOCK_PAL
    return clock / period


def parse_pvd(data):
    """Parse and validate a .pvd file; returns a metadata dict."""
    md = {}
    if len(data) < HEADER_SIZE:
        raise PvdError(f"file too small: {len(data)} bytes < {HEADER_SIZE}")
    if data[0] != MAGIC_LEN:
        raise PvdError(f"string length byte {data[0]:#04x} != {MAGIC_LEN:#04x}")
    if data[1 : 1 + MAGIC_LEN] != MAGIC:
        raise PvdError(f"magic mismatch: {data[1:1+MAGIC_LEN]!r}")
    md["magic"] = data[1 : 1 + MAGIC_LEN].decode("ascii")
    md["version"] = data[0x13]
    md["payload_len_field"] = (
        data[0x14] | (data[0x15] << 8) | (data[0x16] << 16)
    )
    md["period_byte"] = data[0x17]
    payload = data[HEADER_SIZE:]
    md["payload_len_actual"] = len(payload)
    if md["payload_len_actual"] != md["payload_len_field"]:
        raise PvdError(
            f"payload length field {md['payload_len_field']} != "
            f"actual {md['payload_len_actual']} (filesize-24)"
        )
    # Structural delimiters: first/last payload byte 0x00 in all 5 samples.
    md["has_0x00_delimiters"] = (
        len(payload) >= 2 and payload[0] == 0x00 and payload[-1] == 0x00
    )
    if md["has_0x00_delimiters"]:
        md["audio"] = payload[1:-1]
    else:
        md["audio"] = payload
    md["audio_len"] = len(md["audio"])
    # Embedded RIFF/WAVE detection (BOMB.PVD case).
    md["embedded_riff"] = parse_embedded_riff(md["audio"])
    # Stereo pairing heuristic (WAV-imported blobs): odd/even sample
    # equality.  Exact equality >= 60% indicates interleaved duplicated
    # channels rather than a native mono recording.
    x = md["audio"]
    if md["audio_len"] >= 4:
        pairs = sum(
            1 for i in range(0, md["audio_len"] - 1, 2) if x[i] == x[i + 1]
        )
        md["exact_pair_fraction"] = round(pairs / (md["audio_len"] // 2), 4)
    else:
        md["exact_pair_fraction"] = None
    return md


def parse_embedded_riff(audio):
    """Detect and partially parse a RIFF/WAVE header at the start of audio.

    Walks the chunk list properly (id at pos, size at pos+4, payload after),
    so odd fmt sizes or extra chunks cannot desync the "data" lookup.
    """
    if len(audio) < 44 or audio[0:4] != b"RIFF" or audio[8:12] != b"WAVE":
        return None
    fmt = None
    data_chunk = None
    pos = 12
    while pos + 8 <= len(audio):
        cid = audio[pos : pos + 4]
        try:
            csize = struct.unpack_from("<I", audio, pos + 4)[0]
        except struct.error:
            break
        if cid == b"fmt " and fmt is None and pos + 8 + 16 <= len(audio):
            (fmt_tag, channels, rate, byte_rate, block_align, bits) = (
                struct.unpack_from("<HHIIHH", audio, pos + 8)
            )
            fmt = {
                "fmt_chunk_size": csize,
                "format_tag": fmt_tag,
                "channels": channels,
                "declared_rate": rate,
                "byte_rate": byte_rate,
                "block_align": block_align,
                "bits_per_sample": bits,
            }
        elif cid == b"data" and data_chunk is None:
            data_chunk = {"data_size_field": csize, "data_at": pos + 8}
        pos += 8 + csize + (csize & 1)  # RIFF chunks are word-aligned
        if csize == 0 and cid not in (b"fmt ", b"data"):
            break  # avoid infinite loop on a zero-size non-audio chunk
    if fmt is None:
        return None
    available = 0
    truncated = False
    if data_chunk:
        available = max(len(audio) - data_chunk["data_at"], 0)
        truncated = data_chunk["data_size_field"] > available
    return {
        "riff_size_field": struct.unpack_from("<I", audio, 4)[0],
        **fmt,
        "data_size_field": data_chunk["data_size_field"] if data_chunk else None,
        "data_size_available": available,
        "truncated": truncated,
    }


def audio_to_pcm16(audio, zero_floor=False):
    """Unsigned 8-bit PCM -> signed 16-bit little-endian PCM.

    Default mapping (b - 128) * 256 (standard unsigned->signed conversion;
    the 0x7F silence floor then sits at -256, i.e. -42 dBFS DC, inaudible).
    --zero-floor maps (b - 127) * 257 so that the observed 0x7F floor maps
    to exactly 0 and all values stay inside int16.
    """
    offset = 127 if zero_floor else 128
    scale = 257 if zero_floor else 256
    values = [(b - offset) * scale for b in audio]
    return bytearray(struct.pack(f"<{len(values)}h", *values))


def write_wav(path, pcm16, rate, channels=1):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(bytes(pcm16))


def audio_stats(audio):
    """Basic audio statistics, stdlib only (no numpy)."""
    n = len(audio)
    if n == 0:
        return {"n_samples": 0}
    silence = sum(1 for b in audio if b == SILENCE_BYTE)
    dup = sum(1 for i in range(1, n) if audio[i] == audio[i - 1])
    # Zero crossings: strict sign changes of (byte - 128), with samples
    # exactly at 128 treated as neutral (sign 0; a run touching 128 counts
    # one crossing when it moves between strictly positive and strictly
    # negative sides).
    def _sgn(v):
        return (v > 0) - (v < 0)
    signs = [_sgn(b - 128) for b in audio]
    zc = sum(
        1 for i in range(1, n)
        if signs[i] * signs[i - 1] == -1
    )
    centered = [b - 128 for b in audio]
    mean = sum(centered) / n
    rms = (sum(c * c for c in centered) / n) ** 0.5
    peak = max(abs(c) for c in centered)
    return {
        "n_samples": n,
        "silence_fraction_0x7F": round(silence / n, 4),
        "duplicate_fraction": round(dup / (n - 1), 4),
        "zero_crossings_per_sample": round(zc / n, 4),
        "mean_byte_minus_128_dc": round(mean, 3),
        "rms_lsb": round(rms, 2),
        "peak_lsb": peak,
        "min_byte": min(audio),
        "max_byte": max(audio),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Decode ProLine Voice Data (.pvd) to 16-bit WAV."
    )
    ap.add_argument("input", help="input .pvd file")
    ap.add_argument("-o", "--output", help="output .wav path")
    ap.add_argument(
        "--rate", type=int, default=DEFAULT_RATE,
        help=f"sample rate for the WAV (default {DEFAULT_RATE} = PAL Paula "
             f"period {DEFAULT_PERIOD}; alternatives: 20685 NTSC, 8000, "
             f"11025 for WAV-imported blobs)",
    )
    ap.add_argument(
        "--ntsc", action="store_true",
        help=f"use NTSC Paula clock ({PAULA_CLOCK_NTSC // DEFAULT_PERIOD} Hz "
             f"at period {DEFAULT_PERIOD})",
    )
    ap.add_argument(
        "--mode", choices=["raw", "embedded"], default="raw",
        help="raw = decode audio bytes as mono PCM at --rate (default); "
             "embedded = if the audio embeds a RIFF/WAVE header, honour its "
             "declared rate/channels (BOMB.PVD case)",
    )
    ap.add_argument(
        "--stereo", action="store_true",
        help="treat audio as interleaved 2-channel PCM (for WAV-imported "
             "blobs; halves the frame count)",
    )
    ap.add_argument(
        "--zero-floor", action="store_true",
        help="map the 0x7F silence floor to exactly 0 instead of the "
             "standard (b-128)*256 mapping",
    )
    ap.add_argument(
        "--keep-delimiters", action="store_true",
        help="do not strip the structural 0x00 first/last payload bytes",
    )
    ap.add_argument("--no-wav", action="store_true", help="parse only")
    ap.add_argument(
        "--json", action="store_true", help="print metadata+stats as JSON"
    )
    args = ap.parse_args(argv)

    rate = PAULA_CLOCK_NTSC // DEFAULT_PERIOD if args.ntsc else args.rate

    data = Path(args.input).read_bytes()
    md = parse_pvd(data)
    audio = data[HEADER_SIZE:] if args.keep_delimiters else md["audio"]
    md["rate_used"] = rate

    out_path = args.output or (
        Path(args.input).with_suffix(".wav").name
    )
    channels = 1
    emb = md["embedded_riff"]
    if args.mode == "embedded":
        if emb is None:
            print("warning: --mode embedded but no embedded RIFF header "
                  "found; falling back to raw", file=sys.stderr)
        else:
            rate = emb["declared_rate"]
            channels = emb["channels"]
            md["rate_used"] = rate
    if args.stereo:
        channels = 2

    pcm16 = audio_to_pcm16(audio, zero_floor=args.zero_floor)
    n_frames = len(audio) // channels
    stats = audio_stats(audio)
    stats["rate"] = rate
    stats["channels"] = channels
    stats["duration_s"] = round(n_frames / rate, 4)

    if not args.no_wav:
        write_wav(out_path, pcm16, rate, channels)

    report = {
        "file": args.input,
        "magic": md["magic"],
        "version": md["version"],
        "payload_len_field": md["payload_len_field"],
        "payload_len_actual": md["payload_len_actual"],
        "has_0x00_delimiters": md["has_0x00_delimiters"],
        "period_byte": md["period_byte"],
        "period_rate_pal": round(paula_rate(md["period_byte"]), 1),
        "period_rate_ntsc": round(
            paula_rate(md["period_byte"], ntsc=True), 1
        ),
        "exact_pair_fraction": md["exact_pair_fraction"],
        "embedded_riff": emb,
        "wav_written": None if args.no_wav else str(out_path),
        "stats": stats,
    }
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        emb_note = ""
        if emb:
            emb_note = (
                f" [embedded RIFF: {emb['channels']}ch {emb['declared_rate']}Hz "
                f"{emb['bits_per_sample']}bit, declared data "
                f"{emb['data_size_field']}B vs {emb['data_size_available']}B "
                f"present -> {'TRUNCATED' if emb['truncated'] else 'ok'}]"
            )
        print(
            f"{args.input}: v{md['version']} payload {md['payload_len_field']}B "
            f"(audio {md['audio_len']}B) period=0x{md['period_byte']:02X} "
            f"rate={rate}Hz dur={stats['duration_s']}s{emb_note}"
        )
        if not args.no_wav:
            print(f"  wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
