import struct, sys

MAGIC = b"DiamondWare Music\x00"
HDR_UNK6 = bytes.fromhex("001a58a9f6b2")
DRUM_PATCH = bytes.fromhex("21314f00f2d25273000006")
LADDER = [513, 544, 576, 611, 647, 685, 726, 769, 815, 864, 915, 969]
DRUM_VOICE = {35: (6, (15, 3)), 42: (7, (201, 7))}

def read_ibk(path):
    d = open(path, "rb").read()
    assert d[:4] == b"IBK\x1a", "not an IBK bank"
    return {i: d[4 + 16 * i: 4 + 16 * i + 11] for i in range((len(d) - 4) // 16)}

def parse_midi(data):
    hlen = struct.unpack_from(">I", data, 4)[0]
    pos = 8 + hlen
    tracks = []
    while data[pos:pos + 4] == b"MTrk":
        tlen = struct.unpack_from(">I", data, pos + 4)[0]
        tracks.append(data[pos + 8:pos + 8 + tlen]); pos += 8 + tlen
    merged = []
    for ti, t in enumerate(tracks):
        evs = []; tick = 0; i = 0; run = 0
        while i < len(t):
            v = 0
            while True:
                b = t[i]; i += 1
                v = (v << 7) | (b & 0x7F)
                if not b & 0x80: break
            tick += v
            if t[i] & 0x80: st = t[i]; i += 1
            else: st = run
            run = st
            if st == 0xFF:
                mt = t[i]; i += 1
                n = 0
                while True:
                    b = t[i]; i += 1
                    n = (n << 7) | (b & 0x7F)
                    if not b & 0x80: break
                dat = t[i:i + n]; i += n
                evs.append((tick, 0xFF, mt, dat)); continue
            if st in (0xF0, 0xF7):
                n = 0
                while True:
                    b = t[i]; i += 1
                    n = (n << 7) | (b & 0x7F)
                    if not b & 0x80: break
                i += n; continue
            typ = st & 0xF0; ch = st & 0x0F
            if typ in (0x80, 0x90): evs.append((tick, ch, "note", typ, t[i], t[i + 1])); i += 2
            elif typ == 0xB0: evs.append((tick, ch, "cc", t[i], t[i + 1])); i += 2
            elif typ == 0xC0: evs.append((tick, ch, "prog", t[i])); i += 1
            elif typ == 0xD0: i += 1
            elif typ == 0xE0: i += 2
            else: i += 1
        for si, e in enumerate(evs):
            merged.append((e[0], ti, si, e))
    merged.sort(key=lambda x: (x[0], x[1], x[2]))
    tempo = 600000
    for tick, ti, si, e in merged:
        if e[1] == 0xFF and e[2] == 0x51:
            tempo = struct.unpack(">I", b"\x00" + e[3])[0]; break
    return merged, tempo

def hd(tick):
    return (tick * 9 + 24) // 50

def pitch_pair(note):
    idx = (note - 31) % 12
    block = 1 + (note - 31) // 12
    fnum = LADDER[idx]
    return (fnum & 255, (block << 2) | (fnum >> 8))

def encode(mid_path, ibk_path, out_path):
    ibk = read_ibk(ibk_path)
    data = open(mid_path, "rb").read()
    merged, tempo = parse_midi(data)
    progs = {}
    for tick, ti, si, e in merged:
        if e[2] == "prog" and e[1] != 9 and e[1] not in progs: progs[e[1]] = e[3]
    mel_chans = sorted({e[1] for _, _, _, e in merged if e[2] == "note" and e[1] != 9})
    patch_table = [DRUM_PATCH]
    patch_of = {}
    for c in mel_chans:
        slot = progs.get(c, 0)
        if slot not in patch_table[1:]:
            patch_table.append(slot)
        patch_of[c] = patch_table.index(slot)
    records = []
    playing = {v: None for v in range(6)}
    busy_until = {v: -1 for v in range(6)}
    vpatch = {v: 0 for v in range(6)}
    chan_last = {}
    dropped = 0
    for tick, ti, si, e in merged:
        if e[2] != "note": continue
        ch, typ, note, vel = e[1], e[3], e[4], e[5]
        hb = hd(tick)
        if ch == 9:
            if typ == 0x90 and vel > 0:
                if note in DRUM_VOICE: v, w = DRUM_VOICE[note]
                else:
                    v = 9
                    w = pitch_pair(note)
                records.append((hb, len(records), [0x00, v, vel >> 1, w[0], w[1]]))
            continue
        if typ == 0x90 and vel > 0:
            free = [v for v in range(6) if playing[v] is None and hb > busy_until[v]]
            p = patch_of.get(ch, 0)
            pred = None
            if free:
                cl = chan_last.get(ch)
                if cl in free and vpatch[cl] == p: pred = cl
                else:
                    mp = [v for v in free if vpatch[v] == p]
                    wp = [v for v in free if vpatch[v] != 0]
                    np_ = [v for v in free if vpatch[v] == 0]
                    pred = mp[0] if mp else (wp[0] if wp else (np_[0] if np_ else None))
            if pred is None:
                dropped += 1
                continue
            if vpatch[pred] != p:
                records.append((hb, len(records), [0x03, p, pred]))
                vpatch[pred] = p
            w = pitch_pair(note)
            records.append((hb, len(records), [0x00, pred, vel >> 1, w[0], w[1]]))
            playing[pred] = (ch, note)
            chan_last[ch] = pred
        else:
            for v in range(6):
                if playing[v] == (ch, note):
                    records.append((hb - 1, len(records), [0x02, v]))
                    playing[v] = None
                    busy_until[v] = hb + 1
    def cls(params):
        return 0 if params[0] == 0x00 and params[1] >= 6 else 1
    records.sort(key=lambda r: (r[0], cls(r[2]), r[1]))
    body = bytearray()
    prev = 0
    for hb, seq, params in records:
        d = hb - prev
        assert 0 <= d <= 255, "delta overflow at hb %d" % hb
        body.append(d); body += bytes(params); prev = hb
    hdr = bytearray()
    hdr += MAGIC + HDR_UNK6
    hdr += struct.pack("<II", len(body), len(records))
    hdr += struct.pack("<II", 52, 96)
    hdr += struct.pack("<HHHH", 720, len(patch_table), 1, 0x0100)
    hdr += struct.pack("<I", 6)
    for p in patch_table:
        hdr += ibk[p] if isinstance(p, int) else p
    assert len(hdr) == 96
    open(out_path, "wb").write(bytes(hdr) + bytes(body))
    return len(records), dropped

if __name__ == "__main__":
    n, drops = encode(sys.argv[1], sys.argv[2], sys.argv[3])
    print("records", n, "dropped", drops)
