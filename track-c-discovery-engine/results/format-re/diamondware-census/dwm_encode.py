import struct, sys

def read_ibk(path):
    d = open(path, "rb").read()
    assert d[:4] == b"IBK\x1a", "not an IBK bank"
    slots = {}
    for i in range((len(d) - 4) // 16):
        slots[i] = d[4 + 16 * i: 4 + 16 * i + 11]
    return slots

def smf_events(data):
    hlen = struct.unpack_from(">I", data, 4)[0]
    fmt, ntrk, div = struct.unpack_from(">HHH", data, 8)
    pos = 8 + hlen
    ev = []
    while pos < len(data):
        if data[pos:pos + 4] != b"MTrk":
            pos += 1
            continue
        tlen = struct.unpack_from(">I", data, pos + 4)[0]
        t = data[pos + 8: pos + 8 + tlen]
        pos += 8 + tlen
        tick = 0
        i = 0
        run = 0
        while i < len(t):
            v = 0
            while True:
                b = t[i]; i += 1
                v = (v << 7) | (b & 0x7F)
                if not b & 0x80:
                    break
            tick += v
            if t[i] & 0x80:
                st = t[i]; i += 1
            else:
                st = run
            run = st
            if st == 0xFF:
                mt = t[i]; i += 1
                n = 0
                while True:
                    b = t[i]; i += 1
                    n = (n << 7) | (b & 0x7F)
                    if not b & 0x80:
                        break
                dat = t[i:i + n]; i += n
                if mt == 0x51:
                    ev.append((tick, -1, "tempo", struct.unpack(">I", b"\x00" + dat)[0]))
                continue
            if st in (0xF0, 0xF7):
                n = 0
                while True:
                    b = t[i]; i += 1
                    n = (n << 7) | (b & 0x7F)
                    if not b & 0x80:
                        break
                i += n
                continue
            typ = st & 0xF0
            ch = st & 0x0F
            if typ in (0x80, 0x90):
                ev.append((tick, ch, "note", typ, t[i], t[i + 1])); i += 2
            elif typ == 0xB0:
                ev.append((tick, ch, "cc", t[i], t[i + 1])); i += 2
            elif typ == 0xC0:
                ev.append((tick, ch, "prog", t[i])); i += 1
            elif typ == 0xD0:
                i += 1
            elif typ == 0xE0:
                i += 2
            else:
                i += 1
    return div, ev

HB_PER_TICK = None

def quantize(tick):
    return int(round(tick * HB_PER_TICK))

def encode_dwm(mid_path, ibk_path, out_path, rate_decihz=720):
    global HB_PER_TICK
    ibk = read_ibk(ibk_path)
    data = open(mid_path, "rb").read()
    div, ev = smf_events(data)
    tempo = 600000
    for e in ev:
        if e[2] == "tempo":
            tempo = e[3]
            break
    HB_PER_TICK = rate_decihz / 10.0 * tempo / 1e6 / div

    progs = {}
    ons = []
    for e in ev:
        tick, ch = e[0], e[1]
        if e[2] == "prog":
            progs.setdefault(ch, e[3])
        elif e[2] == "note" and e[3] == 0x90 and e[5] > 0:
            ons.append((tick, ch, e[4], e[5]))
    chans = sorted(progs.keys(), key=lambda c: (c == 9, c))
    slots = []
    slot_of = {}
    for ch in chans:
        prog = progs.get(ch, 0)
        idx = 0 if ch == 9 else prog
        if idx not in slots:
            slots.append(idx)
        slot_of[ch] = slots.index(idx)

    drum_voice = {35: 6, 42: 7, 40: 9}
    recs = []
    for tick, ch, note, vel in sorted(ons, key=lambda x: (quantize(x[0]), 0 if x[1] == 9 else 1, x[2])):
        t = quantize(tick)
        vol = vel >> 1
        recs.append([t, ch, note, vol])

    hdr = bytearray()
    hdr += b"DiamondWare Music\x00"
    hdr += struct.pack("<II", 0, len(recs))
    hdr += struct.pack("<II", 52, 52 + 11 * 4)
    hdr += struct.pack("<H", rate_decihz)
    hdr += struct.pack("<H", len(slots))
    hdr += bytes(12)
    patches = bytearray(11 * 4)
    for i, s in enumerate(slots):
        patches[11 * i: 11 * (i + 1)] = ibk[s]
    body = bytearray()
    prev = 0
    for t, ch, note, vol in recs:
        d = min(t - prev, 255)
        prev = t
        if ch == 9:
            v = drum_voice.get(note, 6)
            body += bytes([d, 0x00, v, vol, 0x00, 0x00])
        else:
            body += bytes([d, 0x00, slot_of[ch], vol, 0x00, 0x00])
    body += bytes([0, 0x0B, 0, 0])
    struct.pack_into("<I", hdr, 0x18, len(body))
    open(out_path, "wb").write(bytes(hdr) + bytes(patches) + bytes(body))
    return len(recs)

def decode_events(data):
    return data[96:]

if __name__ == "__main__":
    n = encode_dwm(sys.argv[1], sys.argv[2], sys.argv[3])
    print("wrote", sys.argv[3], "with", n, "note events")
