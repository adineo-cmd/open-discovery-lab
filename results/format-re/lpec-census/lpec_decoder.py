import sys, json

PACKET = 1024
HDR = 10

MODES = {
    "lpec_lp_6000": {"frame_bits": 384, "frame_bytes": 48, "rate_hz": 8000, "subframes": 2,
                     "packing": "per_packet_reset", "frames_per_full_packet": 21},
    "lpec_sp_16000": {"frame_bits": 1024, "frame_bytes": 128, "rate_hz": 16000, "subframes": 2,
                      "packing": "continuous_straddle"},
}


class BitReader:
    """MSB-first bit reader, matching LPEC pump FUN_1000ef20 byte/bit order."""

    def __init__(self, data, bitpos=0):
        self.data = data
        self.pos = bitpos

    def read(self, n):
        v = 0
        for _ in range(n):
            byte = self.data[self.pos >> 3]
            bit = (byte >> (7 - (self.pos & 7))) & 1
            v = (v << 1) | bit
            self.pos += 1
        return v


def audio_packets(raw):
    off = 0x400
    if raw[0x400:0x800] == b"\xff" * 0x400:
        off = 0x800
    pkts = []
    while off + PACKET <= len(raw):
        used = int.from_bytes(raw[off + 4:off + 6], "big")
        if used < HDR or off + used > len(raw):
            break
        pkts.append({"off": off, "used": used, "data": raw[off + HDR:off + used]})
        if used < PACKET:
            break
        off += PACKET
    return pkts


def parse_frames(pkts, mode):
    fb = mode["frame_bits"]
    frames = []
    if mode["packing"] == "continuous_straddle":
        blob = b"".join(p["data"] for p in pkts)
        br = BitReader(blob)
        n = len(blob) * 8 // fb
        for k in range(n):
            start = k * fb
            br.pos = start
            f = {"frame": k, "type": br.read(2), "block": None, "subframes": []}
            if f["type"] == 0:
                f["block"] = br.read(1)
                for _ in range(mode["subframes"]):
                    if br.read(1):
                        f["subframes"].append({"pgidx": br.read(7)})
                    else:
                        f["subframes"].append({"pgidx": None})
            frames.append(f)
    else:
        for pi, p in enumerate(pkts):
            d = p["data"]
            nfull = len(d) * 8 // fb
            br = BitReader(d)
            for k in range(nfull):
                start = k * fb
                br.pos = start
                f = {"pkt": pi, "idx": k, "type": br.read(2), "block": None, "subframes": []}
                if f["type"] == 0:
                    f["block"] = br.read(1)
                    for _ in range(mode["subframes"]):
                        if br.read(1):
                            f["subframes"].append({"pgidx": br.read(7)})
                        else:
                            f["subframes"].append({"pgidx": None})
                frames.append(f)
    return frames


def summarize(frames):
    types = {}
    pg = []
    nsub = 0
    nflag = 0
    for f in frames:
        types[f["type"]] = types.get(f["type"], 0) + 1
        for s in f.get("subframes", []):
            nsub += 1
            if s["pgidx"] is not None:
                nflag += 1
                pg.append(s["pgidx"])
    out = {"frames": len(frames), "type_hist": types,
           "subframes_total": nsub, "subframes_with_codebook": nflag,
           "pgidx_present_ratio": round(nflag / nsub, 4) if nsub else None,
           "pgidx_min": min(pg) if pg else None, "pgidx_max": max(pg) if pg else None,
           "pgidx_mean": round(sum(pg) / len(pg), 2) if pg else None}
    return out


def main():
    path, mode_name = sys.argv[1], sys.argv[2]
    mode = MODES[mode_name]
    raw = open(path, "rb").read()
    pkts = audio_packets(raw)
    frames = parse_frames(pkts, mode)
    print(json.dumps({"file": path.split("/")[-1], "mode": mode_name,
                      "packets": len(pkts), "summary": summarize(frames)}, indent=1))


if __name__ == "__main__":
    main()
