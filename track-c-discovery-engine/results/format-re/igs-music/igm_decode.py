#!/usr/bin/env python3
"""
igm_decode.py — decoder for the IGS .igm binary music stream (F-41).

USAGE:
  python3 -I igm_decode.py --events FILE.igm      # print decoded event list
  python3 -I igm_decode.py --json FILE.igm        # emit JSON summary
  python3 -I igm_decode.py --mid OUT.mid FILE.igm # also write a MIDI file (raw ticks)

Grammar (derived in F-41, see docs/igm-music-grammar.md):
  Container: one or more `N>1,<len>,` headers (first usually `G#N>1,...`),
  each followed by exactly <len> bytes of event-stream data. Chunks
  concatenate into ONE continuous event stream (a record may straddle a
  chunk boundary; the next `N>` header sits in the file between the halves).

  Event stream, big-endian records:
    0x90..0x94  note event, 6 bytes: [status, f1, pitch, f3, dur, delta]
                status  = 0x90 + channel (channels 0..4 observed)
                f1      = flag, 0/1 (meaning unresolved)
                pitch   = raw MIDI note number (36..87 observed; 0 on rests)
                f3      = flag, 0/1 (meaning unresolved)
                dur     = 0x57 (87) on note-attacks, 0x00 on note-releases
                delta   = ticks until the next event (delta 255 seen; ASCII
                          long-delta form suspected but unproven)
    0xC0..0xD0  control events (4- or 10-byte forms observed; semantics open)
    0xFE 0x00   end-of-song marker
  Compressed 4-byte form [status, f1, dur, delta] (pitch/f3 inherited) is
  emitted for a record straddling a chunk boundary (observed exactly once).
"""
import sys, json, re, struct

DUR_ON  = 0x57   # 87: the constant byte carried by every note-attack seen
END     = 0xFE

def parse_chunks(data):
    """Return (chunks, headers). chunks = list of bytes payload per N> header."""
    chunks = []
    headers = []
    for m in re.finditer(rb'N>(\d+),(\d+),', data):
        declared = int(m.group(2))
        start = m.end()
        payload = data[start:start+declared]
        headers.append({'offset': m.start(), 'args1': m.group(1).decode(),
                        'declared_len': declared, 'got_len': len(payload)})
        chunks.append(payload)
    return chunks, headers

def decode_stream(stream):
    """Walk the concatenated event stream. Returns events + skipped-byte count."""
    events = []
    pos, n = 0, len(stream)
    prev_pitch, prev_f3 = None, None
    skipped = 0
    while pos < n:
        b = stream[pos]
        if 0x90 <= b <= 0x94 and pos + 6 <= n:
            f1, pitch, f3, dur, delta = stream[pos+1:pos+6]
            ok = (f3 in (0,1)) and (dur in (0, DUR_ON)) and f1 in (0,1)
            if ok:
                events.append({'off': pos, 'type': 'note', 'ch': b & 0x0F,
                               'f1': f1, 'pitch': pitch, 'f3': f3,
                               'dur': dur, 'delta': delta})
                if pitch: prev_pitch, prev_f3 = pitch, f3
                pos += 6
                continue
        if 0x90 <= b <= 0x94 and pos + 4 <= n:
            # compressed 4-byte form (chunk-boundary straddle):
            # [status, f1, dur, delta] with pitch/f3 inherited
            f1, dur, delta = stream[pos+1:pos+4]
            if f1 in (0,1) and dur in (0, DUR_ON) and pos+4 < n and 0x90 <= stream[pos+4] <= 0x94:
                events.append({'off': pos, 'type': 'note', 'ch': b & 0x0F,
                               'f1': f1, 'pitch': prev_pitch or 0, 'f3': prev_f3 or 0,
                               'dur': dur, 'delta': delta, 'compressed': True})
                pos += 4
                continue
        if 0xC0 <= b <= 0xD0:
            # control event: 4-byte [cN,0,0,x] or 10-byte form; scan to next
            # 0x9N head or 'N>' boundary
            j = pos + 1
            while j < n and not (0x90 <= stream[j] <= 0x94):
                j += 1
            events.append({'off': pos, 'type': 'control', 'ch': b & 0x1F,
                           'raw': stream[pos:j].hex(' '), 'len': j - pos})
            pos = j
            continue
        if b == END:
            events.append({'off': pos, 'type': 'end', 'raw': stream[pos:pos+2].hex(' ')})
            pos += 2
            continue
        # unknown byte: skip
        events.append({'off': pos, 'type': 'skip', 'byte': b})
        pos += 1
        skipped += 1
    return events, skipped

def timeline(events):
    """Attach absolute tick times and match attacks/releases."""
    t = 0
    active = {}   # (ch,pitch) -> (start_tick, idx); f1 differs on/off -> not a voice id
    notes = []
    unmatched_off = 0
    for i, e in enumerate(events):
        if e['type'] == 'note':
            t += e['delta']
            e['t'] = t
            key = (e['ch'], e['pitch'])
            if e['dur'] == DUR_ON and e['pitch'] > 0:
                active[key] = (t, i)
            elif e['dur'] == 0:
                if key in active:
                    st, si = active.pop(key)
                    notes.append({'on_t': st, 'off_t': t, 'ch': e['ch'],
                                  'pitch': e['pitch'], 'dur_ticks': t - st,
                                  'f1_on': events[si]['f1'], 'f1_off': e['f1'],
                                  'f3_on': events[si]['f3']})
                else:
                    unmatched_off += 1
        else:
            e['t'] = t
    return t, notes, unmatched_off

def write_midi(path, notes, total_ticks):
    """Minimal format-0 MIDI; raw tick values kept as delta ticks, 96 tpqn."""
    tpqn = 96
    evs = []
    for nn in notes:
        evs.append((nn['on_t'],  0x90, nn['ch'], nn['pitch'], 100))
        evs.append((nn['off_t'], 0x80, nn['ch'], nn['pitch'], 0))
    evs.sort(key=lambda x: (x[0], x[1]))
    def varlen(v):
        out = bytearray([v & 0x7F]); v >>= 7
        while v: out.insert(0, 0x80 | (v & 0x7F)); v >>= 7
        return bytes(out)
    body = bytearray()
    last = 0
    for t, st, ch, p, v in evs:
        body += varlen(t - last) + bytes([st | ch, p, v])
        last = t
    body += b'\x00\xff\x2f\x00'
    track = b'MTrk' + struct.pack('>I', len(body)) + bytes(body)
    hdr = b'MThd' + struct.pack('>IHHH', 6, 0, 1, tpqn)
    open(path, 'wb').write(hdr + track)

def main():
    args = sys.argv[1:]
    mid_path = None
    if '--mid' in args:
        i = args.index('--mid'); mid_path = args[i+1]; del args[i:i+2]
    mode = '--events'
    if '--json' in args: mode, args = '--json', [a for a in args if a != '--json']
    elif '--events' in args: args = [a for a in args if a != '--events']
    path = args[-1]
    data = open(path, 'rb').read()
    chunks, headers = parse_chunks(data)
    stream = b''.join(chunks)
    events, skipped = decode_stream(stream)
    total_t, notes, unmatched = timeline(events)
    summary = {
        'file': path, 'size': len(data),
        'chunks': headers,
        'stream_bytes': len(stream),
        'event_count': len(events),
        'note_attacks': sum(1 for e in events if e['type']=='note' and e['dur']==DUR_ON and e['pitch']>0),
        'note_releases': sum(1 for e in events if e['type']=='note' and e['dur']==0 and e['pitch']>0),
        'rest_events': sum(1 for e in events if e['type']=='note' and e['pitch']==0),
        'control_events': sum(1 for e in events if e['type']=='control'),
        'skipped_bytes': skipped,
        'unmatched_releases': unmatched,
        'completed_notes': len(notes),
        'total_ticks': total_t,
        'pitch_min': min((e['pitch'] for e in events if e['type']=='note' and e['pitch']>0), default=None),
        'pitch_max': max((e['pitch'] for e in events if e['type']=='note' and e['pitch']>0), default=None),
        'first_attacks': [e['pitch'] for e in events if e['type']=='note' and e['dur']==DUR_ON and e['pitch']>0][:12],
    }
    if mode == '--json':
        print(json.dumps(summary, indent=1))
        print(json.dumps(notes[:40], indent=1))
    else:
        for k, v in summary.items(): print(f"{k}: {v}")
        print("\nfirst 60 events:")
        for e in events[:60]: print("  ", e)
        if mid_path:
            write_midi(mid_path, notes, total_t)
            print(f"\nMIDI written: {mid_path} ({len(notes)} notes)")

if __name__ == '__main__':
    main()
