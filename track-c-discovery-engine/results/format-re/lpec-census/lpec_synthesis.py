import json
import math
import os
import random
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lpec_decoder as ld

DLL_DEFAULTS = [
    "/tmp/f48/dlls/System/LPEC.dll",
    "C:/Program Files (x86)/Sony/Digital Voice Editor/System/LPEC.dll",
]

PCM_ROUND = 0.5
PULSE_SIGN = 0.6
LSF_MIN_GAP = 0.001


class PE:
    def __init__(self, path):
        self.data = open(path, "rb").read()
        d = self.data
        pe = struct.unpack_from("<I", d, 0x3C)[0]
        nsec = struct.unpack_from("<H", d, pe + 6)[0]
        optsz = struct.unpack_from("<H", d, pe + 20)[0]
        self.base = struct.unpack_from("<I", d, pe + 24 + 28)[0]
        self.secs = []
        so = pe + 24 + optsz
        for _ in range(nsec):
            vsize, va, rsize, ro = struct.unpack_from("<IIII", d, so + 8)
            self.secs.append((va, vsize, ro, rsize))
            so += 40

    def off(self, va):
        rva = va - self.base
        for sva, vsize, ro, rsize in self.secs:
            if sva <= rva < sva + vsize:
                o = ro + (rva - sva)
                if 0 <= o <= len(self.data) - 8:
                    return o
                return None
        return None

    def doubles(self, va, n):
        o = self.off(va)
        if o is None:
            raise ValueError("VA out of file: %s" % hex(va))
        return list(struct.unpack_from("<%dd" % n, self.data, o))

    def ptr(self, va):
        o = self.off(va)
        if o is None:
            raise ValueError("VA out of file: %s" % hex(va))
        return struct.unpack_from("<I", self.data, o)[0]


LSP_STAGE_VA = {8000: [0x10024440, 0x10025840, 0x10026C40, 0x10028040],
                16000: [0x1001B040, 0x1001D040, 0x1001F040, 0x10021040]}
PITCH_F0_VA = {8000: 0x100394D0, 16000: 0x100390D0}
PITCH_ROW_A_VA = {8000: 0x1003C0D0, 16000: 0x100398D0}
PITCH_ROW_B_VA = {8000: 0x1003D0D0, 16000: 0x1003ACD0}
PAGES_PTR_VA = {8000: 0x10042960, 16000: 0x10040910}


class ModeTables:
    def __init__(self, pe, fs):
        self.fs = fs
        self.order = 10 if fs <= 8000 else 16
        self.bands = 8 if fs <= 8000 else 10
        self.sub = 256 if fs <= 8000 else 512
        self.frame = self.sub * 2
        self.stage = []
        for va in LSP_STAGE_VA[fs]:
            self.stage.append([pe.doubles(va + r * self.order * 8, self.order) for r in range(64)])
        self.f0 = pe.doubles(PITCH_F0_VA[fs], 128)
        stride = self.bands * 8
        self.rowA = [pe.doubles(PITCH_ROW_A_VA[fs] + i * stride, self.bands) for i in range(64)]
        self.rowB = [pe.doubles(PITCH_ROW_B_VA[fs] + i * stride, self.bands) for i in range(64)]
        self.pages_va = pe.ptr(PAGES_PTR_VA[fs])


def lsf_to_lpc(lsf, order):
    n = order
    m = n // 2
    w = [2.0 * math.pi * v for v in lsf[:n]]
    p = [1.0]
    q = [1.0]
    for i in range(0, n, 2):
        c1 = -2.0 * math.cos(w[i])
        c2 = -2.0 * math.cos(w[i + 1])
        np = [0.0] * (len(p) + 2)
        for k in range(len(p)):
            np[k] += p[k]
            np[k + 1] += c1 * p[k]
            np[k + 2] += p[k]
        p = np
        nq = [0.0] * (len(q) + 2)
        for k in range(len(q)):
            nq[k] += q[k]
            nq[k + 1] += c2 * q[k]
            nq[k + 2] += q[k]
        q = nq
    p = [p[0]] + [p[i] + p[i - 1] for i in range(1, len(p))] + [p[-1]]
    q = [q[0]] + [q[i] - q[i - 1] for i in range(1, len(q))] + [-q[-1]]
    a = [1.0] * (n + 1)
    for k in range(1, m + 1):
        a[k] = 0.5 * (p[k] + q[k])
        a[n + 1 - k] = 0.5 * (p[k] - q[k])
    return a


def enforce_min_gap(vec, order, lo=0.001, hi=0.499):
    v = list(vec)
    for k in range(order):
        if v[k] < lo:
            v[k] = lo
        if v[k] > hi:
            v[k] = hi
    for k in range(1, order):
        if v[k] < v[k - 1]:
            v[k] = v[k - 1]
    for k in range(1, order):
        if v[k] - v[k - 1] < LSF_MIN_GAP:
            v[k] = v[k - 1] + LSF_MIN_GAP
    return v


def synth_filtered(exc, lsf_prev, lsf_cur, order, steps, y_hist):
    n = len(exc)
    blk = n // steps
    out = [0.0] * n
    ybuf = list(y_hist)
    for s in range(steps):
        t = (s + 1) / steps
        vec = [lsf_prev[k] + (lsf_cur[k] - lsf_prev[k]) * t for k in range(order)]
        a = lsf_to_lpc(vec, order)
        for i in range(s * blk, (s + 1) * blk):
            acc = exc[i]
            for k in range(1, order + 1):
                acc -= a[k] * ybuf[-k]
            ybuf.append(acc)
            out[i] = acc
    return out, ybuf[-order:]


def band_excitation(bands, sub, amp, lag, rng):
    exc = [0.0] * sub
    phase = 0
    for k in range(bands):
        lo = int(k * sub / bands)
        hi = int((k + 1) * sub / bands)
        a = amp[k]
        if lag > 0:
            pos = lo + phase
            while pos < hi:
                exc[pos] += PULSE_SIGN * a
                pos += lag
            phase = pos - hi
        else:
            for i in range(lo, hi):
                exc[i] += a * (rng.random() - 0.5)
    return exc


def crossfade(cur, held, sub):
    out = [0.0] * sub
    half = sub // 2
    for i in range(half):
        wr = i / half
        out[i] = wr * held[i] + (1.0 - wr) * cur[i]
    for i in range(half, sub):
        wr = (sub - i) / half
        out[i] = wr * held[i] + (1.0 - wr) * cur[i]
    return out


def page_blend(cur, held, page, sub):
    half = sub // 2
    out = [0.0] * sub
    seg = half // 4
    for s in range(4):
        w_held = page[3 - s]
        w_cur = page[4 + s]
        base1 = page[0] if page[0] else 1.0
        base2 = page[1] if page[1] else 1.0
        for j in range(s * seg, (s + 1) * seg):
            wr = j / half
            a_h = wr * w_held
            a_c = (1.0 - wr) * w_cur
            den = wr * (w_held / base2) + (1.0 - wr) * (w_cur / base1)
            out[j] = (a_h * held[j] + a_c * cur[j]) / den if den else 0.0
    return out


def decode_file(dvf_path, dll_path, mode, out_wav, norm_peak=0.7):
    pe = PE(dll_path)
    data = open(dvf_path, "rb").read()
    cfg = ld.LP_CFG if mode == "lp" else ld.SP_CFG
    fs = cfg["fs"]
    mt = ModeTables(pe, fs)
    order = mt.order
    bands = mt.bands
    sub = mt.sub
    payloads, packets, endpos = ld.extract_audio(data)
    audio = b"".join(payloads)
    frames = ld.parse_stream(audio, cfg)
    rng = random.Random(1234)
    lsf_prev = [(k + 0.5) * 0.5 / order for k in range(order)]
    y_hist = [0.0] * order
    held = [0.0] * sub
    pcm = []
    stats = {"frames": 0, "types": {}, "clipped": 0, "raw_peak": 0.0,
             "g0_subframes": 0, "pages_present": 0}
    for f in frames:
        if f["invalid"]:
            break
        stats["frames"] += 1
        stats["types"][f["type"]] = stats["types"].get(f["type"], 0) + 1
        idxs = f["lsp"][-1]
        vec = []
        for k in range(order):
            v = mt.stage[0][idxs[0]][k]
            for gi in range(1, len(idxs)):
                v += mt.stage[gi][idxs[gi]][k]
            vec.append(v)
        lsf_cur = enforce_min_gap(vec, order)
        n = mt.frame
        exc_full = [0.0] * n
        gs = f.get("gains", [])
        g1 = gs[0][0] if gs and gs[0][0] is not None else 0
        g2 = gs[1][0] if len(gs) > 1 and gs[1][0] is not None else g1
        stats["g0_subframes"] += (1 if g1 == 0 else 0) + (1 if g2 == 0 else 0)
        excf = f.get("exc", [])
        p1, pg1 = excf[0] if excf else (0, None)
        p2, pg2 = excf[1] if len(excf) > 1 else (0, None)
        stats["pages_present"] += (1 if p1 else 0) + (1 if p2 else 0)
        page_data = {}
        if f["type"] == 0:
            for si, (pr, pgi) in enumerate(((p1, pg1), (p2, pg2))):
                if pr and pgi is not None:
                    page_data[si] = pe.doubles(mt.pages_va + pgi * 64, 8)
        pitches = [f.get("pitch0"), f.get("pitch1")]

        def make_cur(si, gsub):
            pitch = pitches[si]
            if pitch is None:
                return None
            i7, iA, iB = pitch
            rowA = mt.rowA[iA]
            rowB = mt.rowB[iB]
            f0s = mt.f0[i7]
            amp = [max(1e-5, rowB[k] + rowA[k]) * f0s * 1e-3 for k in range(bands)]
            return band_excitation(bands, sub, amp, gsub, rng)

        if f["type"] in (1, 3):
            cur = make_cur(1, g2)
            if cur is None:
                cur = [0.0] * sub
            whole = cur + cur
            exc_full = crossfade(whole, held + held, n)
        else:
            cur0 = make_cur(0, g1)
            cur1 = make_cur(1, g2)
            if cur0 is None:
                cur0 = [0.0] * sub
            if cur1 is None:
                cur1 = [0.0] * sub
            seg0 = page_blend(cur0, held, page_data[0], sub) if 0 in page_data else crossfade(cur0, held, sub)
            held2 = cur0
            seg1 = page_blend(cur1, held2, page_data[1], sub) if 1 in page_data else crossfade(cur1, held2, sub)
            exc_full = seg0 + seg1
        held = cur1
        if f["type"] == 0 and f.get("block"):
            avg = [(lsf_prev[k] + lsf_cur[k]) * 0.5 for k in range(order)]
            part1, y_hist = synth_filtered(exc_full[:sub], lsf_prev, avg, order, 8, y_hist)
            part2, y_hist = synth_filtered(exc_full[sub:], avg, lsf_cur, order, 8, y_hist)
            out = part1 + part2
        else:
            out, y_hist = synth_filtered(exc_full, lsf_prev, lsf_cur, order, 16, y_hist)
        lsf_prev = lsf_cur[:]
        for v in out:
            s = v + PCM_ROUND
            if s > 32767.0:
                stats["clipped"] += 1
                s = 32767.0
            elif s < -32768.0:
                stats["clipped"] += 1
                s = -32768.0
            pcm.append(s)
            if abs(s) > stats["raw_peak"]:
                stats["raw_peak"] = abs(s)
    peak = stats["raw_peak"]
    scale = (norm_peak * 32767.0 / peak) if peak > 0 else 0.0
    ints = [int(v * scale) for v in pcm]
    with open(out_wav, "wb") as w:
        dr = len(ints)
        w.write(b"RIFF" + struct.pack("<I", 36 + dr * 2) + b"WAVEfmt " + struct.pack("<IHHIIHH", 16, 1, 1, fs, fs * 2, 2, 16) + b"data" + struct.pack("<I", dr * 2))
        w.write(struct.pack("<%dh" % dr, *ints))
    stats["scale_applied"] = scale
    stats["duration_s"] = round(len(ints) / fs, 3)
    stats["expected_duration_s"] = round(stats["frames"] * cfg["frame_ms"] / 1000, 3)
    stats["fs"] = fs
    stats["order"] = order
    stats["bands"] = bands
    stats["samples"] = len(ints)
    return stats, pcm


def spectral_stats(pcm, fs):
    n = len(pcm)
    frame = 512
    frames = n // frame
    if frames < 1:
        return {"rms": None}
    energy = sum(v * v for v in pcm) / n
    zc = sum(1 for i in range(1, n) if (pcm[i] >= 0) != (pcm[i - 1] >= 0))
    N = 128
    cent_acc = 0.0
    cents = 0
    for fi in range(0, frames, max(1, frames // 64)):
        seg = pcm[fi * frame:(fi + 1) * frame]
        m = 0.0
        mc = 0.0
        for k in range(1, N // 2):
            acc = 0.0
            for t in range(0, frame, 4):
                acc += seg[t] * math.cos(2 * math.pi * k * t / N)
            mag = abs(acc)
            m += mag
            mc += mag * k
        if m > 0:
            cent_acc += mc / m
            cents += 1
    return {
        "rms": round(math.sqrt(energy), 2),
        "zero_cross_rate": round(zc / max(1, n), 4),
        "mean_spectral_centroid_hz": round(cent_acc / max(1, cents) * fs / N, 1),
        "frames_analyzed": frames,
    }


def main():
    samples = sys.argv[1]
    dll = sys.argv[2] if len(sys.argv) > 2 else DLL_DEFAULTS[0]
    outdir = sys.argv[3] if len(sys.argv) > 3 else "/tmp/lpec-synth/wav"
    results = {}
    for fname, mode in (("budgtele.dvf", "lp"), ("07011600.MSV", "sp")):
        p = os.path.join(samples, fname)
        if not os.path.exists(p):
            continue
        wav = os.path.join(outdir, fname.rsplit(".", 1)[0] + ".decoded.wav")
        stats, pcm = decode_file(p, dll, mode, wav)
        ss = spectral_stats(pcm, stats["fs"])
        results[fname] = {"synthesis": stats, "spectral": ss, "wav": wav}
        print(fname, json.dumps({"synthesis": stats, "spectral": ss}))
    json.dump(results, open(os.path.join(outdir, "synthesis_stats.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
