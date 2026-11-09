#!/usr/bin/env python3
"""extract_ext4.py — extract a directory tree from an ext4 Android partition
image using debugfs per-file `dump` (avoids rdump's chown aborts).

Usage: python3 extract_ext4.py <image.img> </in/image/path> <local/dest>
"""
import os
import re
import subprocess
import sys

# debugfs `ls -l`:  <inode> <mode> (<n>) <uid> <gid> <size> <date> <time> <name>
LSL = re.compile(
    r"^\s*(\d+)\s+(\d+)\s+\(\d+\)\s+\d+\s+\d+\s+(\d+)\s+"
    r"\d{1,2}-\w{3}-\d{4}\s+\d{2}:\d{2}(:\d+)?\s+(.+?)\s*$"
)


def debugfs(image, cmd):
    r = subprocess.run(["debugfs", "-R", cmd, image],
                       capture_output=True, text=True, check=False)
    return r.stdout


def listdir(image, path):
    out = debugfs(image, f"ls -l {path}")
    entries = []
    for line in out.splitlines():
        m = LSL.match(line)
        if not m:
            continue
        inode, mode, size, name = int(m.group(1)), m.group(2), int(m.group(3)), m.group(5).strip()
        if name in (".", ".."):
            continue
        is_dir = mode.startswith("4")  # 040xxx = directory
        entries.append((inode, mode, size, name, is_dir))
    return entries


def walk(image, ipath, dest):
    os.makedirs(dest, exist_ok=True)
    for inode, mode, size, name, is_dir in listdir(image, ipath):
        ip = f"{ipath.rstrip('/')}/{name}"
        dp = os.path.join(dest, name)
        if is_dir:
            walk(image, ip, dp)
        else:
            r = subprocess.run(["debugfs", "-R", f"dump {ip} {dp}", image],
                               capture_output=True, text=True, check=False)
            if not os.path.exists(dp) and "Operation not permitted" in r.stderr:
                print(f"WARN dump failed: {ip}", file=sys.stderr)


def main():
    image, src, dest = sys.argv[1], sys.argv[2], sys.argv[3]
    walk(image, src, dest)
    n = sum(len(files) for _, _, files in os.walk(dest))
    print(f"extracted {n} files → {dest}")


if __name__ == "__main__":
    main()
