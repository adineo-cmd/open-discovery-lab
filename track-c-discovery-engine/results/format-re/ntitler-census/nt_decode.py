import struct, sys, json

SCENE_BASE = 0x244
SCENE_STRIDE = 0x3A
TEXT_OFF = 0x1A
TEXT_LEN = 32

def read_cstr(buf, off, maxlen):
    end = off
    while end < off + maxlen and buf[end] != 0:
        end += 1
    return buf[off:end].decode('ascii', 'replace')

def decode(data):
    if data[:4] != b'BT90':
        raise ValueError('bad magic: %r' % data[:4])
    words = [struct.unpack('>H', data[4 + 2 * i:6 + 2 * i])[0] for i in range(24)]
    effects_mask = (words[14] << 16) | words[15]
    backdrop = read_cstr(data, 0x34, 47)
    title = bytes(c ^ 0xFF for c in data[0x64:0x82]).split(b'\x00')[0].decode('ascii', 'replace')
    font = read_cstr(data, 0x82, 50)
    samples = []
    for k in range(8):
        s = read_cstr(data, 0xB4 + 50 * k, 50)
        if s:
            samples.append({'slot': k, 'path': s})
    scenes = []
    p = SCENE_BASE
    n = len(data)
    while p + 2 <= n:
        w = struct.unpack('>H', data[p:p + 2])[0]
        if w >= 0x8000:
            break
        deltas = [struct.unpack('>h', data[p + 2 + 2 * i:p + 4 + 2 * i])[0] for i in range(5)]
        text = data[p + TEXT_OFF:p + TEXT_OFF + TEXT_LEN].split(b'\x00')[0].decode('ascii', 'replace')
        scenes.append({
            'word0': w,
            'motion_deltas': deltas,
            'word12': struct.unpack('>H', data[p + 0x12:p + 0x14])[0],
            'word14': struct.unpack('>H', data[p + 0x14:p + 0x16])[0],
            'word16': struct.unpack('>H', data[p + 0x16:p + 0x18])[0],
            'word18': struct.unpack('>H', data[p + 0x18:p + 0x1A])[0],
            'text': text,
        })
        p += SCENE_STRIDE
    terminator = data[p:p + 2] == b'\xff\xff' and p + 2 == n
    return {
        'magic': 'BT90',
        'header_words': words,
        'effects_bitmask': '0x%08x' % effects_mask,
        'backdrop_path': backdrop,
        'title_xorff': title,
        'font_path': font,
        'sample_paths': samples,
        'scenes': scenes,
        'eof_law_ok': terminator,
    }

if __name__ == '__main__':
    out = {}
    for path in sys.argv[1:]:
        data = open(path, 'rb').read()
        try:
            out[path] = decode(data)
        except Exception as e:
            out[path] = {'error': str(e)}
    print(json.dumps(out, indent=1))
