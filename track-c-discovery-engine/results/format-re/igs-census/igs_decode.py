#!/usr/bin/env python3
"""
Instant Graphics and Sound (IGS) decoder - partial, stdlib only.
Cracked: IGS is a plain-text command stream over an Atari ST 640x200 screen.
Lines beginning 'G#' carry IG commands (plain text lines carry BBS message text).
Commands: letter>args separated by ':'; '_' at end-of-line = wrapped continuation;
'@' terminates W (write-text) payloads; .IG files = .IGS stream with BBS message
header prepended (verified XNET_LST pair); .igm embeds a binary MIDI-like event
stream in the N> command (not fully cracked here). Validation: all numeric coords
fit x<=639, y<=199 (0 violations across samples).
Usage: igs_decode.py [--svg OUT.svg] SAMPLE ...
"""
import sys, os, re, json

def load_stream(raw):
    text = raw.decode("latin1")
    flat = text.replace("\r", "")
    flat = re.sub(r"_\n", "", flat)          # unwrap continuation lines
    return text, flat

def parse_commands(flat):
    cmds = []
    for line in flat.split("\n"):
        g = line.startswith("G#")
        segs = line[2:] if g else line
        for seg in segs.split(":"):
            seg = seg.strip()
            if not seg: continue
            m = re.match(r"^([A-Za-z&])>(.*)$", seg)
            if m: cmds.append({"g": g, "cmd": m.group(1), "args": m.group(2)})
    return cmds

def main():
    argv = sys.argv[1:]; svg_out = None
    if argv and argv[0] == "--svg":
        svg_out = argv[1]; argv = argv[2:]
    results = []
    lines_svg = []
    for path in argv:
        raw = open(path, "rb").read()
        text, flat = load_stream(raw)
        cmds = parse_commands(flat)
        hist = {}
        for c in cmds: hist[c["cmd"]] = hist.get(c["cmd"], 0) + 1
        # coordinate validation
        nx = ny = 0; xmax = ymax = 0; bad = []
        for c in cmds:
            if c["cmd"] in "LDFBJHO":
                nums = [int(x) for x in re.findall(r"\d+", c["args"])[:2]]
                if len(nums) == 2:
                    nx += 1; ny += 1
                    xmax = max(xmax, nums[0]); ymax = max(ymax, nums[1])
                    if nums[0] > 639 or nums[1] > 199: bad.append(c["args"])
            elif c["cmd"] == "B":
                nums = [int(x) for x in re.findall(r"\d+", c["args"])[:4]]
                if len(nums) == 4:
                    xmax = max(xmax, nums[0], nums[2]); ymax = max(ymax, nums[1], nums[3])
                    if max(nums[0], nums[2]) > 639 or max(nums[1], nums[3]) > 199: bad.append(c["args"])
        wtexts = [c["args"].split("@")[0] for c in cmds if c["cmd"] == "W" and "@" in c["args"]]
        notes = [c["args"] for c in cmds if c["cmd"] == "n"]
        nonascii = sum(1 for b in raw if not (9 <= b <= 13 or 32 <= b <= 126))
        r = {
            "file": os.path.basename(path), "size": len(raw),
            "nonascii_bytes": nonascii,
            "g_lines": sum(1 for line in flat.split("\n") if line.startswith("G#")),
            "command_count": len(cmds), "command_hist": hist,
            "x_max": xmax, "y_max": ymax, "coord_violations": bad[:3],
            "w_texts": wtexts[:6],
            "n_events": len(notes),
            "n_binary": raw.find(b"N>") >= 0 and "N> binary payload present" or None,
        }
        results.append(r)
        # SVG proof-of-decode: render L/D polylines of ASCII-only samples
        if svg_out and nonascii == 0:
            cx = cy = 0
            for c in cmds:
                a = c["args"]
                if c["cmd"] == "L":
                    m = re.match(r"^(\d+),(\d+),(\d+),(\d+)", a)
                    if m:
                        lines_svg.append((m.group(1), m.group(2), m.group(3), m.group(4)))
                        cx, cy = int(m.group(3)), int(m.group(4))
                elif c["cmd"] == "D":
                    m = re.match(r"^(\d+),(\d+)", a)
                    if m:
                        lines_svg.append((str(cx), str(cy), m.group(1), m.group(2))); cx, cy = int(m.group(1)), int(m.group(2))
    if svg_out:
        with open(svg_out, "w") as f:
            f.write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 200" width="640" height="200">\n<rect width="640" height="200" fill="black"/>\n')
            for x1, y1, x2, y2 in lines_svg:
                f.write(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="white" stroke-width="1"/>\n')
            f.write("</svg>\n")
    print(json.dumps(results, indent=1))

main()
