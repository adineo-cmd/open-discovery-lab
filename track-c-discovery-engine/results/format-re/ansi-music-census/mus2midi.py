#!/usr/bin/env python3
"""mus2midi.py - ANSI Music (.mus/.ams) to Standard MIDI File converter.
Open Discovery Lab Track C (F-40, R-10). stdlib only.

Protocol (per ansimtech.txt + dybczak.txt, artscene.textfiles.com/ansimusic/):
  music string = ESC [ M <PLAY-command-string> CTRL-N(0x0E)
  PLAY grammar (GW/Tandy BASIC): A-G [#|+|-], Ln (1-64), On (0-6), Nn (0-84, 0=rest),
  Pn rest, '.' dotted, Tn tempo, MF/MB/MN/ML/MS, '>' '<' octave shift.
Semantics: octave 3 C = middle C = MIDI 60 -> midi = 12*(octave+2)+semitone.
Quarter note = 60/T seconds; whole = 4 quarters; length = (4/L)*(60/T).
MN plays 7/8, ML full, MS 3/4 of L duration. Rests always full length.
Stream semantics: strings play sequentially in file order (terminal transport).
"""
import sys, json, struct, re
from pathlib import Path

SEMI = {'C':0,'D':2,'E':4,'F':5,'G':7,'A':9,'B':11}
MODE = {'MN':7/8,'ML':1.0,'MS':3/4,'MF':7/8,'MB':7/8,'M':7/8}

class State:
    def __init__(s):
        s.octave=4; s.len=4; s.tempo=120; s.mode='MN'
    def qdur(s): return 60.0/s.tempo

def parse_play(txt, st):
    """Returns (events, errors). events: (t_abs_sec, dur_sec, midi_pitch)."""
    ev=[]; t=0.0; i=0; errs=[]; n=len(txt)
    while i<n:
        c=txt[i].upper()
        if c=='T':
            m=re.match(r'\d+', txt[i+1:]);  st.tempo=int(m.group()) if m else 120; i+=1+len(m.group()) if m else 1
        elif c=='L':
            m=re.match(r'\d+', txt[i+1:]);  st.len=int(m.group()) if m else 4; i+=1+len(m.group()) if m else 1
        elif c=='O':
            m=re.match(r'\d+', txt[i+1:]);  st.octave=int(m.group()) if m else 4; i+=1+len(m.group()) if m else 1
        elif c=='N':
            m=re.match(r'\d+', txt[i+1:])
            if m:
                nn=int(m.group()); i+=1+len(m.group())
                if nn==0:
                    d=(4.0/st.len)*st.qdur(); t+=d
                else:
                    midi=24+((nn-1)//12)*12+((nn-1)%12)
                    d=(4.0/st.len)*st.qdur()
                    if st.mode in MODE: d*=MODE[st.mode]
                    while i<n and txt[i]=='.':
                        d*=1.5; i+=1
                    ev.append((t, d, midi)); t+=d
            else: i+=1
        elif c=='P':
            m=re.match(r'\d+', txt[i+1:])
            if m:
                L=int(m.group()); i+=1+len(m.group())
                d=(4.0/L)*st.qdur()
                while i<n and txt[i]=='.':
                    d*=1.5; i+=1
                t+=d
            else: i+=1
        elif c in SEMI:
            j=i+1; acc=0
            while j<n and txt[j] in '#+':
                acc+=1; j+=1
            while j<n and txt[j]=='-':
                acc-=1; j+=1
            midi=12*(st.octave+2)+SEMI[c]+acc
            # optional per-note duration suffix digits (GW-BASIC: C16 = sixteenth)
            m2=re.match(r'\d+', txt[j:])
            L=None
            if m2: L=int(m2.group()); j+=len(m2.group())
            L = L if L is not None else st.len
            d=(4.0/L)*st.qdur()
            while j<n and txt[j]=='.':
                d*=1.5; j+=1
            if st.mode in MODE: d*=MODE[st.mode]
            ev.append((t,d,midi)); t+=d; i=j
        elif c=='M':
            two=txt[i+1:i+3].upper()
            if two in ('MN','ML','MS','MF','MB'): st.mode=two; i+=3
            else: st.mode='M'; i+=2
        elif c=='>': st.octave=min(6,st.octave+1); i+=1
        elif c=='<': st.octave=max(0,st.octave-1); i+=1
        elif c in ' \t': i+=1
        else:
            errs.append(f'char {txt[i]!r}@{i}'); i+=1
    return ev, errs

def extract_sequences(data: bytes):
    """Find ESC[M ... 0x0E music strings; returns list of (playtext, context_line)."""
    seqs=[]; i=0
    while True:
        k=data.find(b'\x1b[M', i)
        if k<0: break
        j=data.find(b'\x0e', k+3)
        if j<0: break
        raw=data[k+3:j]
        ctx=data[max(0,k-24):k]
        seqs.append((raw.decode('latin1'), ctx.decode('latin1','replace')))
        i=j+1
    return seqs

def write_midi(events, path, ppq=480):
    """Type-0 MIDI, single track, 120bpm base (event times already in seconds).
    Returns n_notes."""
    div=ppq
    evs=[]
    for t,d,m in events:
        if m is None: continue
        t0=round(t*2.0*div)
        t1=round((t+d)*2.0*div)
        evs.append((t0,0x90,m,100)); evs.append((t1,0x80,m,0))
    evs.sort()
    tempo=500000
    out=bytearray()
    out+=b'MThd'+struct.pack('>IHHH',6,0,1,div)
    track=bytearray()
    def varl(v):
        b=bytearray()
        b.insert(0, v & 0x7F); v>>=7
        while v: b.insert(0, 0x80|(v & 0x7F)); v>>=7
        return bytes(b)
    track+=varl(0)+b'\xff\x51\x03'+struct.pack('>I',tempo)[1:]
    last=0
    for t0,stat,m,vel in evs:
        track+=varl(t0-last)+bytes([0x90 if stat==0x90 else 0x80, m, vel])
        last=t0
    track+=varl(0)+b'\xff\x2f\x00'
    out+=b'MTrk'+struct.pack('>I',len(track))+track
    Path(path).write_bytes(bytes(out))
    return len(evs)//2

def main():
    res=[]
    for path in sorted(sys.argv[1:]):
        data=Path(path).read_bytes()
        seqs=extract_sequences(data)
        st=State(); allev=[]; allerrs=[]; pitchmin=999; pitchmax=-1
        for txt,ctx in seqs:
            ev,errs=parse_play(txt, st)
            allev+=ev; allerrs+=errs
            for _,_,m in ev:
                pitchmin=min(pitchmin,m); pitchmax=max(pitchmax,m)
        total=allev[-1][0]+allev[-1][1] if allev else 0.0
        mid=path+'.mid'
        nnotes=write_midi(allev, mid) if allev else 0
        res.append(dict(file=Path(path).name, size=len(data),
            n_sequences=len(seqs), n_notes=len(allev),
            total_sec=round(total,2), pitch_range=[pitchmin,pitchmax] if allev else None,
            parse_errors=allerrs[:5], n_parse_errors=len(allerrs),
            midi_out=Path(mid).name, midi_bytes=Path(mid).stat().st_size if allev and Path(mid).exists() else 0))
    print(json.dumps(res, indent=1))

if __name__=='__main__':
    main()
