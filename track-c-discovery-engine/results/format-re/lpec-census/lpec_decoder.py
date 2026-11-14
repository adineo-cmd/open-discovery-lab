import json
import os
import struct
import sys


class BitReader:
    def __init__(self, data, bitpos=0):
        self.data = data
        self.pos = bitpos

    def read(self, n):
        v = 0
        p = self.pos
        for _ in range(n):
            byte = self.data[p >> 3]
            v = (v << 1) | ((byte >> (7 - (p & 7))) & 1)
            p += 1
        self.pos = p
        return v

    def skip(self, n):
        self.pos += n

    def align(self):
        self.pos = (self.pos + 7) & ~7


LP_CFG = {
    "name": "LpecLp",
    "fs": 8000,
    "lsp_groups": 3,
    "lsp_bits": 6,
    "gain_bits": 7,
    "targets": [384, 288, 480, 384],
    "frame_bytes": [48, 36, 60, 48],
    "lpc_order": 10,
    "bands": 8,
    "frame_ms": 64,
}

SP_CFG = {
    "name": "LpecSp",
    "fs": 16000,
    "lsp_groups": 4,
    "lsp_bits": 6,
    "gain_bits": 8,
    "targets": [1024, 768, 1280, 1024],
    "frame_bytes": [128, 96, 160, 128],
    "lpc_order": 16,
    "bands": 10,
    "frame_ms": 64,
}


def div2_toward_zero(x):
    if x < 0:
        return -((-x + 1) >> 1)
    return x >> 1


def read_pitch(r):
    return [r.read(7), r.read(6), r.read(6)]


def parse_frame(r, cfg):
    start = r.pos
    f = {"bit": start}
    consumed = 2
    t = r.read(2)
    f["type"] = t
    inv = None
    if t == 0:
        block = r.read(1)
        consumed += 1
        f["block"] = block
        nsets = 2 if block else 1
        f["lsp"] = [[r.read(cfg["lsp_bits"]) for _ in range(cfg["lsp_groups"])] for _ in range(nsets)]
        consumed += nsets * cfg["lsp_groups"] * cfg["lsp_bits"]
        gains = []
        for _ in range(2):
            g = r.read(cfg["gain_bits"])
            consumed += cfg["gain_bits"]
            sh = None
            if g != 0:
                sh = r.read(6)
                consumed += 6
            gains.append([g, sh])
        f["gains"] = gains
        exc = []
        for _ in range(2):
            p = r.read(1)
            consumed += 1
            pg = None
            if p:
                pg = r.read(7)
                consumed += 7
            exc.append([p, pg])
        f["exc"] = exc
        rem = cfg["targets"][0] - consumed
        if rem < 0:
            inv = "header-overrun"
        else:
            half = div2_toward_zero(rem)
            i7 = [8 if e[0] else 1 for e in exc]
            a0 = half - i7[0]
            a1 = half - i7[1]
            if a0 < 19 or a1 < 19:
                inv = "pulse-budget-negative"
            else:
                f["pitch0"] = read_pitch(r)
                f["pulse0_bits"] = a0 - 19
                r.skip(a0 - 19)
                f["pitch1"] = read_pitch(r)
                f["pulse1_bits"] = a1 - 19
                r.skip(a1 - 19)
                f["tail_skip"] = cfg["targets"][0] - (r.pos - start)
                r.skip(f["tail_skip"])
    elif t in (1, 3):
        f["lsp"] = [[r.read(cfg["lsp_bits"]) for _ in range(cfg["lsp_groups"])]]
        consumed += cfg["lsp_groups"] * cfg["lsp_bits"]
        g = r.read(cfg["gain_bits"])
        consumed += cfg["gain_bits"]
        sh = None
        if g != 0:
            sh = r.read(6)
            consumed += 6
        f["gains"] = [[None, None], [g, sh]]
        a = cfg["targets"][t] - consumed
        if a < 19:
            inv = "pulse-budget-negative"
        else:
            f["pitch1"] = read_pitch(r)
            f["pulse1_bits"] = a - 19
            r.skip(a - 19)
            f["tail_skip"] = cfg["targets"][t] - (r.pos - start)
            r.skip(f["tail_skip"])
    elif t == 2:
        f["lsp"] = [[r.read(cfg["lsp_bits"]) for _ in range(cfg["lsp_groups"])]]
        consumed += cfg["lsp_groups"] * cfg["lsp_bits"]
        gains = []
        for _ in range(2):
            g = r.read(cfg["gain_bits"])
            consumed += cfg["gain_bits"]
            sh = None
            if g != 0:
                sh = r.read(6)
                consumed += 6
            gains.append([g, sh])
        f["gains"] = gains
        c1 = consumed
        rem1 = cfg["targets"][0] - c1
        if rem1 < 19:
            inv = "pulse-budget-negative"
        else:
            a1 = div2_toward_zero(rem1)
            f["pitch0"] = read_pitch(r)
            f["pulse0_bits"] = a1 - 19
            r.skip(a1 - 19)
            c2 = c1 + a1
            a2 = cfg["targets"][2] - c2
            if a2 < 19:
                inv = "pulse-budget-negative"
            else:
                f["pitch1"] = read_pitch(r)
                f["pulse1_bits"] = a2 - 19
                r.skip(a2 - 19)
                f["tail_skip"] = cfg["targets"][2] - (r.pos - start)
                r.skip(f["tail_skip"])
    else:
        inv = "reserved-type"
    f["end_bit"] = r.pos
    f["bytes"] = (r.pos - start + 7) // 8
    f["invalid"] = inv
    return f


def extract_audio(data):
    if data[0x400:0x800] == b"\xff" * 1024:
        pos = 0x800
    else:
        pos = 0x400
    packets = []
    payloads = []
    while pos + 10 <= len(data):
        sizes = struct.unpack_from(">H", data, pos + 4)[0]
        if sizes < 10 or sizes > 1024:
            break
        if data[pos] != 0 or data[pos + 2] != 0 or data[pos + 3] != 0x0A:
            break
        payloads.append(data[pos + 10:pos + sizes])
        packets.append(sizes)
        pos += 1024
        if sizes < 1024:
            break
    return payloads, packets, pos


def parse_stream(audio, cfg):
    frames = []
    r = BitReader(audio)
    total_bits = len(audio) * 8
    while r.pos + 16 <= total_bits:
        f = parse_frame(r, cfg)
        frames.append(f)
        if f["invalid"]:
            break
    return frames


def packet_straddle_stats(frames, payload_lens):
    bounds = []
    off = 0
    for pl in payload_lens:
        off += pl
        bounds.append(off * 8)
    strad = sum(1 for f in frames for b in bounds if f["bit"] < b <= f["end_bit"])
    aligned = sum(1 for b in bounds if any(f["end_bit"] == b for f in frames))
    return {"packet_boundaries": len(bounds), "frames_straddling_boundary": strad, "boundaries_on_frame_end": aligned}


def summarize(frames, cfg):
    types = [f.get("type") for f in frames]
    hist = {t: types.count(t) for t in sorted(set(types))}
    inv = sum(1 for f in frames if f["invalid"])
    size_ok = sum(1 for f in frames if not f["invalid"] and f["bytes"] == cfg["frame_bytes"][f["type"]])
    tail = {}
    for f in frames:
        if f["invalid"]:
            continue
        k = (f["type"], f.get("tail_skip"))
        tail[k] = tail.get(k, 0) + 1
    gains0 = 0
    gains_tot = 0
    for f in frames:
        if f["invalid"]:
            continue
        for g in f.get("gains", []):
            if g[0] is not None:
                gains_tot += 1
                if g[0] == 0:
                    gains0 += 1
    lags = [f["pitch0"][0] for f in frames if not f["invalid"] and f.get("pitch0")]
    lags += [f["pitch1"][0] for f in frames if not f["invalid"] and f.get("pitch1")]
    voiced = 0
    for f in frames:
        if f["invalid"]:
            continue
        for e in f.get("exc", []):
            if e[0]:
                voiced += 1
    lag_continuity = None
    seq = [f["pitch0"][0] for f in frames if not f["invalid"] and f.get("pitch0")]
    if len(seq) > 2:
        d = [abs(seq[i + 1] - seq[i]) for i in range(len(seq) - 1)]
        lag_continuity = {
            "mean_abs_delta": round(sum(d) / len(d), 3),
            "delta_le_2": sum(1 for x in d if x <= 2) / len(d),
        }
    return {
        "frames": len(frames),
        "type_hist": {str(k): v for k, v in hist.items()},
        "invalid": inv,
        "size_matches_expected": size_ok,
        "tail_skip_map": {str(k): v for k, v in tail.items()},
        "gain_zero_rate": round(gains0 / gains_tot, 4) if gains_tot else None,
        "lag_min": min(lags) if lags else None,
        "lag_max": max(lags) if lags else None,
        "lag_continuity": lag_continuity,
        "excitation_present_rate": round(voiced / max(1, sum(1 for f in frames if not f["invalid"] for _ in f.get("exc", []))), 4),
    }


def analyze(path, mode):
    data = open(path, "rb").read()
    cfg = LP_CFG if mode == "lp" else SP_CFG
    payloads, packets, endpos = extract_audio(data)
    audio = b"".join(payloads)
    frames = parse_stream(audio, cfg)
    out = {
        "file": os.path.basename(path),
        "mode": cfg["name"],
        "file_size": len(data),
        "packets": len(packets),
        "packet_sizes_first_last": [packets[0], packets[-1]] if packets else [],
        "audio_bytes": len(audio),
        "container_model": "continuous-bitstream-frames-straddle-packets",
        "packet_straddle": packet_straddle_stats(frames, [len(p) for p in payloads]),
    }
    out["summary"] = summarize(frames, cfg)
    out["byte_closure"] = {
        "frame_bytes_sum": sum(f["bytes"] for f in frames),
        "audio_bytes": len(audio),
        "exact": sum(f["bytes"] for f in frames) == len(audio) and frames and frames[-1]["end_bit"] == len(audio) * 8,
    }
    detail = []
    for i, f in enumerate(frames[:48]):
        d = {"i": i, "t": f["type"], "bytes": f["bytes"]}
        for k in ("block", "lsp", "gains", "exc", "pitch0", "pitch1", "tail_skip"):
            if f.get(k) is not None:
                d[k] = f[k]
        if f["invalid"]:
            d["invalid"] = f["invalid"]
        detail.append(d)
    out["frames_detail_first48"] = detail
    out["frames_detail_last8"] = [{"i": len(frames) - len(frames[-8:]) + j, "t": f["type"], "bytes": f["bytes"]} for j, f in enumerate(frames[-8:])]
    out["type_seq_head"] = [f["type"] for f in frames[:256]]
    out["type_hist_full"] = {str(t): sum(1 for f in frames if f["type"] == t) for t in range(4)}
    out["bitrate_check"] = {
        "frame_ms": cfg["frame_ms"],
        "mean_bits_per_frame": round(sum(cfg["frame_bytes"][f["type"]] for f in frames) * 8 / len(frames), 2),
        "implied_bps": round(sum(cfg["frame_bytes"][f["type"]] for f in frames) * 8 / len(frames) / (cfg["frame_ms"] / 1000), 1),
    }
    return out


def main():
    samples = sys.argv[1]
    outpath = sys.argv[2]
    results = {}
    for fname, mode in (("budgtele.dvf", "lp"), ("07011600.MSV", "sp")):
        p = os.path.join(samples, fname)
        if os.path.exists(p):
            results[fname] = analyze(p, mode)
    json.dump(results, open(outpath, "w"), indent=1)


if __name__ == "__main__":
    main()
