import math, re, sys
from collections import Counter

def be(b, o, n): return int.from_bytes(b[o:o+n], 'big')
def le(b, o, n): return int.from_bytes(b[o:o+n], 'little')

def entropy(bs):
    if not bs: return 0.0
    c = Counter(bs); n = len(bs)
    return -sum((v/n)*math.log2(v/n) for v in c.values())

def find_audio_start(b):
    for o in range(0x400, len(b)-1024, 0x400):
        if b[o+2:o+6] == bytes([0, 0x0a, 4, 0]) or b[o+2:o+4] == bytes([0, 0x0a]):
            return o
    return None

def packet_walk(b, start):
    npkt = (len(b) - start) // 1024
    nns, sizes, triples, counters = [], [], Counter(), Counter()
    last = None
    for k in range(npkt):
        o = start + k * 1024
        nns.append(b[o+1]); sizes.append(be(b, o+4, 2))
        triples[b[o+5:o+9].hex()] += 1
        counters[b[o+9]] += 1
        if sizes[-1] < 1024: last = (k, o, sizes[-1])
    return npkt, nns, sizes, triples, counters, last

def autocorr(data, lo, hi):
    n = len(data)
    out = []
    for s in range(lo, hi+1):
        m = sum(1 for i in range(n-s) if data[i] == data[i+s])
        out.append((m/(n-s), s))
    out.sort(reverse=True)
    return out

def data_stream(b, start, npkt):
    d = bytearray()
    for k in range(npkt):
        o = start + k*1024
        sz = be(b, o+4, 2)
        d += b[o+10:o+sz]
    return bytes(d)

def phase_test(b, start, npkt, period, limit=400):
    hist = Counter()
    for k in range(1, min(npkt-1, limit)):
        o = start + k*1024
        d = b[o+10:o+1024]
        best, bestr = None, -1.0
        for p in range(period):
            seg = d[p:p+period*10]
            m = sum(1 for i in range(len(seg)-period) if seg[i] == seg[i+period])
            r = m/(len(seg)-period)
            if r > bestr: bestr, best = r, p
        hist[best] += 1
    return hist

def bit_profile(d):
    bits = [0]*8
    for by in d:
        for k in range(8):
            if by & (0x80 >> k): bits[k] += 1
    return [x/len(d) for x in bits]

def analyze(name, b):
    print('='*100)
    print(f'FILE {name} size={len(b)}')
    print(f'magic={b[0:8]} codec@0x0c={b[0x0c:0x10].hex()} origin@0x20={b[0x20:0x30].rstrip(bytes([0]))}')
    print(f'submode@0x3c={be(b,0x3c,2)} bitrate@0x40={be(b,0x40,4)} bytes_per_s@0x44={be(b,0x44,4)}')
    for i in range(0x50, 0xb0, 8):
        tag, val = le(b, i, 4), be(b, i+4, 4)
        if tag == 4:
            print(f'  TOC@0x{i:02x} tag4: unused_tail={int.from_bytes(b[i+1:i+4],"big")} audio_bytes={be(b,i+4,4)}')
        elif 0 < tag < 0x80:
            print(f'  TOC@0x{i:02x} tag={tag} value={val}')
    start = find_audio_start(b)
    print(f'audio_start=0x{start:x}')
    npkt, nns, sizes, triples, counters, last = packet_walk(b, start)
    print(f'packets={npkt} size_field_histogram={Counter(sizes).most_common(4)}')
    print(f'NN[:30]={" ".join(f"{x:02x}" for x in nns[:30])}')
    print(f'header_triples={dict(triples)} counter_bytes_top={counters.most_common(4)}')
    if last:
        k, o, sz = last
        print(f'last_partial_packet={k} @0x{o:x} size={sz} audio_end=0x{o+sz:x} post_audio={len(b)-(o+sz)}B')
    d = data_stream(b, start, npkt)
    print(f'data_stream_bytes={len(d)} entropy={entropy(d):.3f}')
    top = autocorr(d[:min(len(d), 300000)], 8, 200)
    print('autocorr top10:', [(s, round(r, 4)) for r, s in top[:10]])
    for cand in (24, 48, 128):
        hist = phase_test(b, start, npkt, cand, limit=200)
        print(f'phase test period={cand}:', dict(sorted(hist.items())[:8]))
    for F in (24, 48):
        n = len(d)//F
        ds = []
        for i in range(min(n-1, 20000)):
            ds.append(sum(bin(x ^ y).count('1') for x, y in zip(d[i*F:(i+1)*F], d[(i+1)*F:(i+2)*F]))/(F*8))
        print(f'consecutive-frame bit-diff F={F}: {sum(ds)/max(1,len(ds)):.4f}')
    print(f'bit_profile P(1): {" ".join(f"{x:.3f}" for x in bit_profile(d[:200000]))}')
    cands = []
    for k in range(npkt):
        o = start + k*1024
        blk = b[o+10:o+1024]
        ff = mx = 0
        for x in blk:
            ff = ff+1 if x == 0xff else 0
            mx = max(mx, ff)
        if mx < 128:
            cands.append((entropy(blk[-384:]), k))
    cands.sort()
    print('lowest-entropy packets:', [(k, round(e, 3)) for e, k in cands[:4]])
    strs = re.findall(rb'[ -~]{4,}', b[:start])
    print('pre-audio strings:', [s.decode() for s in strs][:8])

if __name__ == '__main__':
    d = sys.argv[1] if len(sys.argv) > 1 else '/tmp/lpec/samples'
    for name in ['07011600.MSV', 'WelcometoPinkstonMiddleSchoolLibrarytest.dvf', 'budgtele.dvf', 'taxis.dvf']:
        with open(f'{d}/{name}', 'rb') as f:
            analyze(name, f.read())
